# resrun: Restic Runner
Generate and run Restic commands from a TOML config. 
When running through resrun, the output is logged to disk.

**This project is *very* WIP. Stuff may be broken, not implemented or untested.
DO NOT RUN ON YOUR REAL RESTIC REPOSITORY without checking the generated commands carefully.**
## TODO
- [x] Basic config loading
- [x] Command generation (partial)
  - [x] Backup
  - [x] Batch backup
  - [x] Copy
  - [x] Forget
  - [x] Manual
- [ ] Tests
- [ ] Doit integration