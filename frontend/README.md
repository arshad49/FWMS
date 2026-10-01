# frontend

[![n8n](https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)](https://n8n.io)
[![flat8n](https://img.shields.io/badge/flat8n-FF6E4A.svg)](https://github.com/jvondev/flat8n)

A modern n8n workflow project, scaffolded with `create-n8n`.

## Development

Run the dev server (automatically starts a local n8n instance and watches your files for changes):

```bash
npm run dev
```

## Build

Compile your modular workflows into a single deployable monolithic JSON workflow:

```bash
npm run build
```

## Architecture

Your source workflows are in the `workflows/` directory.
Shared or reusable logic goes in `workflows/subworkflows/`.
