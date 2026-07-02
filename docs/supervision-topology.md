# Supervision topology: user — observer — conductor — workers

Most agent pipelines put the user in direct conversation with the
orchestrator. We stopped doing that. The standard topology here is four
layers:

```
user ── observer (talks to the user, only observes the system)
            │ reads artifacts on disk; writes protocol artifacts at boundaries
            ▼
        conductor (Maestro, unattended; context contains protocol + disk state, nothing else)
            │ dispatches, one experiment = one fresh agent
            ▼
        workers (Coder, Auditor, Runner, ... — fresh context per experiment)
```

The point is not efficiency or division of labor. The point is that the
conductor's context stays sterile.

## Why user chat is contamination

A conductor that chats with the user mid-run absorbs things that have no
place in a preregistered pipeline: casual scope changes, emotional tone,
and — worst — hints about which result the user would like. Language models
are sycophantic; "I feel like the effect should be bigger" from the user is
often enough to bend an analysis. Behavioral science has a name for the
human version: experimenter demand effects. Preregistration protects
verdicts from data-driven bias; keeping the user out of the conductor's
context protects them from user-driven bias. Same blinding discipline, two
directions.

The user is protected too. They can ask anything, any time, in any tone —
it all terminates at the observer. Nobody has to remember not to disturb a
running experiment; the structure remembers for them.

## The three channel rules

1. **Read without disturbing.** The observer answers user questions from
   disk artifacts only: the conductor's status brief, the dispatch log, the
   knowledge tree, decision files. Reading these costs the conductor
   nothing; it never learns the question was asked. This covers almost all
   user interaction ("how is it going", "what did that verdict mean").

2. **Influence enters as protocol artifacts, at boundaries.** When the user
   actually wants to change direction, the observer translates the request
   into the pipeline's own formats — an amended task file, a tree
   annotation, a config change — and writes it to disk. It takes effect at
   the next experiment boundary, when a fresh agent rebuilds its context
   from disk. Nothing is ever injected into a running agent's conversation.
   The injection point coincides with the context-rebuild point of the
   one-experiment-one-agent rule (big-finding, principle 4), so influence
   and fresh context always arrive together.

3. **Correct by respawn, not by conversation.** If the observer sees a
   protocol violation (a pooled metric, a skipped audit, an unaudited
   number in the ledger), it does not message the agent to argue. A context
   that produced a violation is no longer trustworthy after a scolding
   either. Kill the agent, tighten the task file so the violation can't
   recur, dispatch a fresh one. The only message the observer may send
   directly is a content-free wake signal ("the run you were waiting on
   finished") — a timer, not an opinion.

## Context allocation by decision horizon

Each layer holds only the state its decisions need, which keeps every layer
in the model's short-context regime where quality is highest:

| Layer | Decision horizon | Context contains | Token profile |
|---|---|---|---|
| observer | the whole program + user intent | briefs, ledgers, verdicts | small, judgment-dense |
| conductor | one pipeline | protocol + pipeline state | medium, no raw transcripts |
| worker | one experiment | one task file + pointers | small, fresh every time |

A worker never sees another experiment's transcript (that's principle 4).
The conductor never reads worker transcripts, only structured outputs. The
observer never reads the conductor's transcript, only its disk artifacts.
Every hop between layers is a file with a schema, not a conversation — this
is what stops the topology from degrading into a game of telephone.

## When not to use four layers

Depth should scale with risk and duration. A typo fix needs one agent. Add
a layer when the layer below saturates: a worker's context can't hold the
pipeline → add a conductor; the conductor runs unattended for hours and the
user needs a safe way to watch and steer → add an observer. The topology is
a ceiling, not a floor.

## Escalation path

The conductor never contacts the user. When it hits a stop condition
(defined in its task: budget overruns, repeated audit failures, anything
irreversible), it writes an ESCALATION section into its status brief and
ends its turn. The observer relays the decision brief to the user, gets an
answer, translates it into a protocol artifact, and the next fresh context
picks it up from disk. The user's words never touch the conductor.

Related: `skills/big-finding/SKILL.md` (principle 4, one experiment one
agent), `skills/research-autonomy-contract/SKILL.md` (which actions may
proceed without asking a human).
