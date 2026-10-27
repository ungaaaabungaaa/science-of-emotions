# Reading emotion research carefully

## Separate measurement from interpretation

A person can report an experience, an observer can label a text, and a camera can measure facial movement. These are different measurements. An emotion inference needs evidence connecting the measurement to the interpretation in its intended context.

GoEmotions studies labels assigned to language. Its annotations support language research, but this lab's label count is not a count of people experiencing that emotion. [Demszky et al., 2020](https://aclanthology.org/2020.acl-main.372/).

## Useful categories can have fuzzy boundaries

Cowen and Keltner studied reports elicited by short videos and found a rich structure with continuous transitions between some reported experiences. Their categories, stimuli, and self-report methods differ from the text annotations used here. The shared number 27 does not make the measurements interchangeable. [Original PNAS study, 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5617253/).

## A cue does not establish a mental state

A review of facial movements found substantial variation across people and contexts, limiting simple one-to-one emotion inferences. It concerns facial measurements and does not validate this text dataset. It illustrates why observations and conclusions need separate treatment. [Barrett et al., 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6640856/).

## Ask a limited, testable question

This project checks label rates and overlaps across known splits. Its rules and denominators are explicit. Readers can rerun the code, inspect hashes, and change labels in the viewer. Its claim is bounded by the measured data.

For future work, state the target task, measurement, population, comparison, and failure conditions before training a model. Use held-out data, report per-label results and uncertainty, and test the intended context. Annotation agreement and benchmark scores do not establish a general ability to understand people.
