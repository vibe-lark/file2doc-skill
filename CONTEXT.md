# File2Doc Context

This context describes the File2Doc skill used to turn offline attachments into structured inputs for Lark document writing.

## Language

**File2Doc Service**:
The online HTTP service that accepts an uploaded offline file and produces Markdown, manifest metadata, media artifacts, thumbnails, page images, video frames, transcripts, and timelines.
_Avoid_: local converter, local parser, preprocessing script

**Parse Job**:
A server-side asynchronous parsing task created by uploading a file stream to `POST /parse-jobs/upload`.
_Avoid_: conversion run, script run

**Manifest**:
The structured JSON result returned by `GET /parse-jobs/{job_id}/result`. It is the source of truth for artifact IDs, media index entries, transcript metadata, and timelines.
_Avoid_: guessed file path, generated output directory

**Artifact**:
A downloadable service result addressed by `artifact_id`, such as Markdown content, thumbnails, page images, video frames, or transcript files.
_Avoid_: service path, local output path

**Media Index**:
The manifest section that lists available visual or media artifacts, including thumbnails, page images, embedded images, and video frames.
_Avoid_: screenshot list, frame list

**Thumbnail**:
A low-cost visual preview used by an Agent to understand document structure before deciding which high-detail page images are needed.
_Avoid_: full page screenshot

**Page Image**:
A rendered page artifact for document-like inputs. Page images are fetched selectively and may be regenerated at supported DPI levels.
_Avoid_: mandatory screenshot dump

**Video Frame**:
A representative frame artifact associated with timeline metadata.
_Avoid_: raw frame extraction

**Caller-Side Path**:
A path that exists on the Agent or caller machine. File2Doc receives uploaded file bytes; it does not read caller-side paths itself.
_Avoid_: server local path
