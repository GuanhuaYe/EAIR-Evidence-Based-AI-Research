# ACL ARR Responsible NLP Checklist

ACL / EMNLP / NAACL via ARR requires this checklist plus an explicit
Limitations section. Skipping causes desk-reject risk.

## A. For every submission

A1. Did you discuss the limitations of your work?
A2. Did you discuss any potential risks of your work?
A3. Do the abstract and introduction summarize the paper's main
    claims?
A4. Have you used AI writing assistance (e.g., ChatGPT, Copilot) in
    any way? If so, where?

## B. Use of scientific artifacts

B1. Did you cite the creators of artifacts you used?
B2. Did you discuss the license or terms for use of the artifacts?
B3. Did you discuss whether your use of existing artifact(s) was
    consistent with their intended use?
B4. Did you discuss the steps taken to check whether the data
    contains personally identifying information or offensive content?
B5. Did you provide documentation of the artifacts (e.g., coverage of
    domains, languages, demographics)?
B6. Did you report relevant statistics (e.g., size of train/test
    splits, average length)?

## C. Computational experiments

C1. Did you report the number of parameters in the models used, the
    total computational budget (e.g., GPU hours), and computing
    infrastructure used?
C2. Did you discuss the experimental setup, including hyperparameter
    search and best-found hyperparameter values?
C3. Did you report descriptive statistics about your results
    (e.g., error bars around results, summary statistics from sets of
    experiments), and is it transparent whether you are reporting the
    max, mean, etc.?
C4. Did you report a summary of the computational packages used (e.g.,
    libraries with versions)?

## D. Human subjects and annotators

D1. Did you report the full text of instructions given to participants,
    including e.g., screenshots, disclaimers of any risks, and full
    annotation instructions?
D2. Did you report information about how you recruited (e.g., crowd-
    sourcing platform, students), the demographic of annotators, and
    paid compensation?
D3. Did you discuss whether and how consent was obtained from people
    whose data you're using/curating?
D4. Was the data collection protocol approved (or determined exempt)
    by an ethics review board?
D5. Did you report basic demographic and geographic characteristics
    of the annotator population?

## E. Use of AI assistants

If A4 is yes, specify the assistant, the role (e.g., grammar
checking, code generation), and any oversight applied.

## Limitations section

ACL ARR requires an explicit Limitations section. Must include:
- Scope of generalizations claimed (and where they break down)
- Computational / environmental cost honest reporting
- Datasets / languages / demographics not covered
- Failure modes observed
- Threats to validity for any human evaluation
