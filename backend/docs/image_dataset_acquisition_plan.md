# SATYA image dataset acquisition and provenance plan

## Executive summary

SATYA needs three evaluation categories—`authentic`, `manipulated`, and
`synthetic`—but UnivFD is a binary detector trained and evaluated as
`0_real` versus `1_fake`. It is therefore appropriate as one binary signal,
especially for authentic-versus-AI-generated evaluation, but it cannot by
itself establish the distinction between manipulated and synthetic images or
produce a validated three-class result.

This document defines a small, traceable acquisition plan. It does not
download, copy, or populate any dataset. No dataset license should be treated
as permitting redistribution until the applicable official terms have been
reviewed and recorded.

The initial target is up to 300 images:

| SATYA category | Target |
|---|---:|
| authentic | 100 |
| manipulated | 100 |
| synthetic | 100 |

These are targets, not collected samples. If a source cannot supply a
well-documented category, the final evaluation must report the actual
available counts rather than filling the gap with relabeled or fabricated
samples.

## Repository state

Inspected:

- `backend/scripts/evaluate_univfd.py`
- `backend/scripts/univfd_inference.py`
- `backend/tests/test_univfd_evaluation.py`
- `backend/models/image/fc_weights.pth`
- repository data directories and dataset-related documentation

The evaluator already:

- discovers images from `authentic`, `manipulated`, and `synthetic` folders;
- records relative paths, scores, durations, device, and errors;
- preserves failed samples in its report;
- refuses evaluation artifacts when there is no valid evaluation data;
- requires explicit binary-direction information for binary metrics.

The runner and evaluator are CUDA-only and use the existing UnivFD checkpoint.
There is currently no `backend/data/` directory, no labeled validation set,
and no metadata manifest in the repository. No data was downloaded in this
phase.

## Candidate dataset comparison

### GenImage

- **Official sources:** [repository](https://github.com/GenImage-Dataset/GenImage),
  [project page](https://genimage-dataset.github.io/), and
  [paper](https://arxiv.org/abs/2306.08571).
- **Purpose:** Large-scale detection of AI-generated images.
- **Authentic data:** Yes. The official layout calls this `nature`, collected
  from ImageNet content.
- **Synthetic data:** Yes. The official layout calls this `ai` and includes
  domains such as Midjourney, Stable Diffusion, ADM, GLIDE, Wukong, VQDM, and
  BigGAN.
- **Manipulated data:** No dedicated manipulated-real category is documented.
- **Original labels:** `ai` and `nature`, with generator-specific directories
  and train/validation organization.
- **Size:** The official project describes more than one million fake/real
  pairs; the full resource is much larger than the initial target.
- **Access:** The official repository points to hosted archives; access may
  require following the provider's download process.
- **License and commercial use:** License verification required. The repository
  does not establish a universal commercial-use or redistribution permission
  for every underlying image.
- **Redistribution:** Not assumed. Verify terms for the downloaded archive and
  its underlying source images.
- **SATYA suitability:** Include as the primary synthetic source and a possible
  authentic source, with original labels retained.
- **Limitations:** Binary AI-generated versus natural content; it does not
  represent splicing, copy-move, object removal, or other manipulated-real
  categories.

### UnivFD / CNNDetection evaluation data

- **Official sources:** [UniversalFakeDetect](https://github.com/Yuheng-Li/UniversalFakeDetect),
  [CNNDetection](https://github.com/PeterWang512/CNNDetection), and the
  [UnivFD paper](https://arxiv.org/abs/2302.10174).
- **Purpose:** Reproduce UnivFD-style real-versus-fake evaluation across
  multiple generative domains.
- **Authentic data:** Yes, under `0_real`.
- **Synthetic data:** Yes, under `1_fake`, across GAN, diffusion, and related
  generator domains documented by UnivFD.
- **Manipulated data:** Not as an independent SATYA category. Some domains may
  contain content described as deepfake or other generated content, but those
  original labels must not be collapsed into `manipulated` without source
  documentation.
- **Original labels:** `0_real` and `1_fake`.
- **Size:** UnivFD documents approximately 19 GB for the CNNDetection test
  collection and smaller released diffusion subsets; exact counts depend on
  the selected domain/archive.
- **Access:** Hosted downloads and archive-specific instructions are provided
  by the official projects.
- **License and commercial use:** License verification required for the
  datasets and underlying images. The UnivFD code repository is MIT licensed,
  but that does not grant rights to the image datasets.
- **Redistribution:** Not assumed. Do not commit or redistribute downloaded
  images without confirming each dataset's terms.
- **SATYA suitability:** Include for checkpoint-convention verification and
  authentic-versus-synthetic evaluation.
- **Limitations:** It does not provide SATYA's independent manipulated class;
  it may also expose domain or generator bias.

### CASIA image tampering dataset

- **Official source:** [CASIA tampering database portal](http://forensics.idealtest.org/#/).
- **Purpose:** Image tampering detection and localization research.
- **Authentic data:** Yes, paired with forged examples.
- **Synthetic data:** No independent AI-generation category is established.
- **Manipulated data:** Yes, including documented tampering types such as
  splicing, copy-move, and removal, depending on the release.
- **Original labels:** Authentic/forged and, for applicable releases,
  manipulation masks or localization annotations.
- **Size:** Do not use third-party counts as an acquisition fact. Record the
  exact release and manifest count after lawful access.
- **Access:** Obtain through the official portal or an explicitly authorized
  release.
- **License and commercial use:** License verification required. Academic or
  research availability must not be interpreted as commercial permission.
- **Redistribution:** Not assumed; verify the official release terms and any
  separate mask annotations.
- **SATYA suitability:** Include as a manipulation source if the required
  release and terms are approved.
- **Limitations:** Older tampering styles, dataset-specific artifacts, and
  limited representation of modern AI editing. Do not relabel forged images as
  synthetic.

### Columbia image splicing dataset

- **Official source:** [Columbia DVMM authenticated/spliced dataset](https://www.ee.columbia.edu/ln/dvmm/downloads/AuthSplicedDataSet/AuthSplicedDataSet.htm).
- **Purpose:** Authenticated versus spliced image-forensics evaluation.
- **Authentic data:** Yes.
- **Synthetic data:** No independent AI-generation category.
- **Manipulated data:** Yes, specifically splicing.
- **Original labels:** Authenticated/spliced, with the release's documented
  image or block-level labeling.
- **Size:** Verify from the official release manifest after access; no
  unverified count is used in this plan.
- **Access:** The official page controls access and provides dataset terms.
- **License and commercial use:** License verification required. Research
  access does not imply commercial use.
- **Redistribution:** Not assumed; follow the official no-redistribution or
  attribution conditions if applicable.
- **SATYA suitability:** Optional manipulation-only source for a focused
  splicing evaluation.
- **Limitations:** Narrow manipulation coverage and possible block-level
  labeling differences; not a synthetic-image source.

### NIST OpenMFC

- **Official sources:** [NIST Open Media Forensics Challenge](https://www.nist.gov/itl/iad/mltg/open-media-forensics-challenge)
  and [OpenMFC portal](https://mfc.nist.gov/).
- **Purpose:** Evaluation of image/video manipulation detection and
  localization, with challenge-specific forensic tasks.
- **Authentic data:** Available as part of challenge-specific comparisons,
  subject to the release and task.
- **Synthetic data:** Some tasks support GAN-related manipulation detection,
  but this is not equivalent to a general AI-generated-image category.
- **Manipulated data:** Yes, including task-specific manipulation and
  localization data.
- **Original labels:** Challenge/task-specific image-level, localization,
  manipulation-type, or related forensic annotations.
- **Size:** Varies by challenge; use the official release manifest rather than
  a cross-challenge estimate.
- **Access:** Registration and completion of license agreements are required
  for released datasets.
- **License and commercial use:** License verification required. Commercial
  use is not assumed.
- **Redistribution:** Not assumed; NIST states that access is controlled and
  agreements apply.
- **SATYA suitability:** Optional, potentially strong manipulation evaluation
  source after access and legal review.
- **Limitations:** Access overhead, task-specific labels, and no direct
  three-class SATYA mapping.

### Recommendation summary

| Candidate | Authentic | Manipulated | Synthetic | Recommendation |
|---|---|---|---|---|
| GenImage | Yes (`nature`) | No | Yes (`ai`) | Include |
| UnivFD/CNNDetection | Yes (`0_real`) | No independent class | Yes (`1_fake`) | Include |
| CASIA | Yes | Yes | No | Include after terms review |
| Columbia | Yes | Yes, splicing | No | Optional |
| NIST OpenMFC | Task-dependent | Yes | Task-dependent GAN tasks | Optional after access review |

## Initial 300-image evaluation target

The proposed target is:

- 100 authentic images.
- 100 manipulated images.
- 100 synthetic images.

This target is feasible only if the relevant source terms and labels are
verified. The practical source plan is:

1. **Synthetic:** Select 100 `ai`/`1_fake` images from one or more documented
   GenImage or UnivFD generator domains. Preserve generator identity and the
   original binary label.
2. **Authentic:** Select 100 matched or independently documented `nature`/
   `0_real` images from the same approved source family where possible.
3. **Manipulated:** Select 100 CASIA samples, or an approved Columbia/NIST
   subset, retaining the original manipulation label and method.

If a legally usable manipulation subset cannot be obtained, the feasible first
evaluation is binary authentic-versus-synthetic only. It must not fill the
manipulated target with synthetic images.

### Leakage and duplicate controls

- Preserve source dataset IDs and parent-image IDs.
- Compute SHA-256 for exact duplicate detection.
- Use perceptual hashes for near-duplicate detection.
- Keep an original and all of its edits in the same split.
- Keep all variants derived from one parent image together.
- Do not place the same prompt/source image or generator-family duplicate in
  both threshold-calibration and final-test sets.
- Keep generator and manipulation method fields for source-aware analysis.
- Do not mix the same real image from GenImage with a manipulated derivative
  in a different split.

### Calibration and final test

Use a separate threshold-calibration subset and final test subset. A practical
plan is:

- Calibration: 40–50 samples per available binary class/category.
- Final test: the remaining samples, ideally at least 50 per category.

Thresholds must be selected only on calibration data. The final test set must
remain untouched until the threshold and reporting protocol are fixed. If the
dataset is too small for this separation, report score distributions only and
avoid an unbiased threshold-performance claim.

## Dataset manifest

Recommended file:

```text
data/image_validation/metadata.csv
```

Required schema:

```text
sample_id
relative_path
modality
ground_truth_category
original_dataset
original_label
source_id
source_url
manipulation_method
generator_name
parent_image_id
split
license
license_url
collection_date
notes
```

### Field rules

- `sample_id`: Required; stable local identifier.
- `relative_path`: Required; path below the validation root only.
- `modality`: Required; `image`.
- `ground_truth_category`: Required SATYA evaluation category, only after
  documented mapping.
- `original_dataset`: Required.
- `original_label`: Required; preserve the source label unchanged.
- `source_id`: Required where supplied by the source; otherwise explain in
  `notes`.
- `source_url`: Required for the official dataset or item identifier when
  available.
- `manipulation_method`: Required for manipulated samples when known;
  otherwise blank with an explanation.
- `generator_name`: Required for synthetic samples when known; otherwise
  blank with an explanation.
- `parent_image_id`: Required when an edit or generated derivative has a
  known parent; otherwise blank.
- `split`: Required; for example `calibration` or `test`.
- `license`: Required; use the exact applicable term or
  `license verification required`.
- `license_url`: Required when a public terms page exists.
- `collection_date`: Required; ISO date when acquired.
- `notes`: Optional, but use it for unresolved provenance or transformations.

Do not replace `original_label` with `ground_truth_category`. A source
`1_fake`, `ai`, or `spliced` label must remain visible even when a documented
SATYA mapping is added.

## Data quality checklist

Before evaluation:

- Confirm every manifest row has a readable relative path.
- Reject missing files.
- Decode each image with Pillow and verify that it is not corrupt.
- Convert supported grayscale/RGBA files to RGB only at inference time.
- Record unsupported formats and failed decodes instead of dropping them.
- Verify the extension agrees with the decoded format, or record the mismatch.
- Compute and store SHA-256 hashes for exact duplicate detection.
- Compute perceptual hashes for near-duplicate review.
- Check for repeated `source_id`, `parent_image_id`, prompt, or generator
  leakage across splits.
- Check that every row has an original label and dataset source.
- Check that every row has a license decision or an explicit unresolved
  license status.
- Review manipulation masks or source annotations where applicable.
- Verify no personal absolute paths occur in metadata or reports.
- Compare category mappings against official source definitions.
- Record removals and rejection reasons in a separate audit log.

## Licensing and provenance cautions

- The UnivFD source code license does not automatically license its image
  datasets.
- “Research use” does not imply commercial use.
- Public download availability does not imply redistribution permission.
- Hosted archives may combine images with different source terms.
- Keep attribution, citation, and license URLs with each source.
- Do not commit downloaded images, archives, credentials, or personal paths.
- Obtain explicit approval before downloading even a small subset.
- If terms cannot be confirmed, do not use the sample for a public or
  commercial evaluation artifact.

## Recommended acquisition order

1. **Verify the binary detector convention.** Use a small approved set with
   explicit UnivFD-style `0_real` and `1_fake` labels. This tests the local
   checkpoint against its expected task without changing the model.
2. **Acquire authentic and synthetic samples.** Start with a small,
   source-balanced GenImage or UnivFD-compatible subset. Report this as
   authentic-versus-synthetic/fake evaluation only.
3. **Acquire manipulated samples separately.** Use CASIA first if its terms
   and annotations are approved; otherwise evaluate Columbia or NIST access.
   Preserve `spliced`, `copy-move`, `removal`, or task-specific labels.
4. **Run score-distribution analysis.** Use the existing evaluator and report
   all errors and category distributions.
5. **Calibrate only a binary threshold.** Do this on a dedicated calibration
   split after confirming the direction and sufficient sample size.
6. **Assess three-category compatibility.** Do not map the binary score to
   `authentic`, `manipulated`, and `synthetic` unless a separately validated
   method exists.

## Explicit limitations

- UnivFD is not a manipulation-localization model.
- UnivFD does not distinguish manipulated from AI-generated content.
- The score is not calibrated.
- A threshold selected on one source or generator may not transfer.
- A 300-image target is an initial evaluation plan, not a benchmark.
- Dataset artifacts, compression, generator identity, and source imbalance
  can dominate results.
- Exact license and count details must be recorded from the approved release
  actually acquired.
- No dataset or evaluation result exists in this repository yet.

## Recommended next steps

After approval, select the exact archives and licenses, then acquire only the
approved small subset. Populate the manifest before running inference. Run
the existing evaluator without changing the model or API, produce separate
binary and manipulation analyses, and report whether the manipulated sample
distribution is distinguishable from authentic and synthetic samples. Do not
start API integration or claim three-class detection from this evaluation.
