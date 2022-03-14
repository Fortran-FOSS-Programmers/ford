# Changelog

## [v6.1.9](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.9) (2022-03-14)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.1.8...v6.1.9)

**Fixed bugs:**

- FORD tries to run the preprocessor even if preprocessor test failed [\#398](https://github.com/Fortran-FOSS-Programmers/ford/issues/398)
- exclude\_dir is broken in 6.1.8 [\#391](https://github.com/Fortran-FOSS-Programmers/ford/issues/391)
- Preprocessing broken? [\#389](https://github.com/Fortran-FOSS-Programmers/ford/issues/389)
- Derived Types header missing [\#388](https://github.com/Fortran-FOSS-Programmers/ford/issues/388)
- source display broken [\#387](https://github.com/Fortran-FOSS-Programmers/ford/issues/387)

**Closed issues:**

- ford-6.1.8 test: test\_projects/test\_external\_project.py is broken  [\#395](https://github.com/Fortran-FOSS-Programmers/ford/issues/395)
- Ugly tables in markdown pages [\#373](https://github.com/Fortran-FOSS-Programmers/ford/issues/373)

**Merged pull requests:**

- Fix external project test [\#397](https://github.com/Fortran-FOSS-Programmers/ford/pull/397) ([ZedThree](https://github.com/ZedThree))
- External projects: deal with extended types [\#396](https://github.com/Fortran-FOSS-Programmers/ford/pull/396) ([haraldkl](https://github.com/haraldkl))
- Fix `exclude_dirs` [\#394](https://github.com/Fortran-FOSS-Programmers/ford/pull/394) ([ZedThree](https://github.com/ZedThree))
- Fix for preprocessors that can't read from stdin [\#393](https://github.com/Fortran-FOSS-Programmers/ford/pull/393) ([ZedThree](https://github.com/ZedThree))
- Fix `type` permission attributes [\#392](https://github.com/Fortran-FOSS-Programmers/ford/pull/392) ([ZedThree](https://github.com/ZedThree))
- Fix showing source in generated docs [\#390](https://github.com/Fortran-FOSS-Programmers/ford/pull/390) ([ZedThree](https://github.com/ZedThree))
- Update math and environ markdown extensions [\#385](https://github.com/Fortran-FOSS-Programmers/ford/pull/385) ([ZedThree](https://github.com/ZedThree))
- Fix CSS for markdown tables and add optional striped-table extension [\#384](https://github.com/Fortran-FOSS-Programmers/ford/pull/384) ([ZedThree](https://github.com/ZedThree))

## [v6.1.8](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.8) (2022-02-01)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.1.7...v6.1.8)

**Fixed bugs:**

- Fails with TypeError for preprocessing file [\#380](https://github.com/Fortran-FOSS-Programmers/ford/issues/380)

**Closed issues:**

- LaTeX macros [\#361](https://github.com/Fortran-FOSS-Programmers/ford/issues/361)
- Installing on macOS Big Sur [\#351](https://github.com/Fortran-FOSS-Programmers/ford/issues/351)

**Merged pull requests:**

- Fix local external project [\#382](https://github.com/Fortran-FOSS-Programmers/ford/pull/382) ([ZedThree](https://github.com/ZedThree))
- Fix preprocessor command [\#381](https://github.com/Fortran-FOSS-Programmers/ford/pull/381) ([ZedThree](https://github.com/ZedThree))

## [v6.1.7](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.7) (2022-01-31)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.1.6...v6.1.7)

**Merged pull requests:**

- Fix multiline attributes [\#379](https://github.com/Fortran-FOSS-Programmers/ford/pull/379) ([ZedThree](https://github.com/ZedThree))
- Fix black action to work on forks; only run on changes to .py files [\#376](https://github.com/Fortran-FOSS-Programmers/ford/pull/376) ([ZedThree](https://github.com/ZedThree))
- deps: need `importlib-metadata` [\#375](https://github.com/Fortran-FOSS-Programmers/ford/pull/375) ([chenrui333](https://github.com/chenrui333))
- Tidy up and refactor initialisation [\#365](https://github.com/Fortran-FOSS-Programmers/ford/pull/365) ([ZedThree](https://github.com/ZedThree))

## [v6.1.6](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.6) (2022-01-04)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.1.5...v6.1.6)

**Fixed bugs:**

- 'str object' has no attribute 'meta' - error when abstract interface imported from different module [\#372](https://github.com/Fortran-FOSS-Programmers/ford/issues/372)

**Merged pull requests:**

- add asterisks to list of mangled symbols [\#374](https://github.com/Fortran-FOSS-Programmers/ford/pull/374) ([chucklesoclock](https://github.com/chucklesoclock))

## [v6.1.5](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.5) (2021-09-23)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.1.4...v6.1.5)

**Closed issues:**

- Question: comment in project file? [\#210](https://github.com/Fortran-FOSS-Programmers/ford/issues/210)

**Merged pull requests:**

- Enable aliases in docstrings [\#363](https://github.com/Fortran-FOSS-Programmers/ford/pull/363) ([ZedThree](https://github.com/ZedThree))
- Fixed module variable INTRINSIC\_MODS being changed implicitly.  [\#362](https://github.com/Fortran-FOSS-Programmers/ford/pull/362) ([byornski](https://github.com/byornski))
- Make sure "Find us on" present if `project_gitlab` set [\#359](https://github.com/Fortran-FOSS-Programmers/ford/pull/359) ([d7919](https://github.com/d7919))
- Fixed invalid check for : character in extra\_mods. [\#358](https://github.com/Fortran-FOSS-Programmers/ford/pull/358) ([byornski](https://github.com/byornski))

## [v6.1.4](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.4) (2021-09-13)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.1.3...v6.1.4)

**Implemented enhancements:**

- pybuilder and test coverage [\#13](https://github.com/Fortran-FOSS-Programmers/ford/issues/13)

**Fixed bugs:**

- Footnotes in Pages [\#327](https://github.com/Fortran-FOSS-Programmers/ford/issues/327)
- Code blocks don't seem to work within subroutines [\#287](https://github.com/Fortran-FOSS-Programmers/ford/issues/287)
- Markdown headers do not work as expected [\#286](https://github.com/Fortran-FOSS-Programmers/ford/issues/286)

**Merged pull requests:**

- Fix indentation in markdown blocks and footnotes appearing on multiple pages [\#356](https://github.com/Fortran-FOSS-Programmers/ford/pull/356) ([ZedThree](https://github.com/ZedThree))

## [v6.1.3](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.3) (2021-09-10)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.1.2...v6.1.3)

**Fixed bugs:**

- Case sensitivity for MODULE SUBROUTINE [\#353](https://github.com/Fortran-FOSS-Programmers/ford/issues/353)
- Release 6.0.0 does not contain `ford/js/MathJax-config` [\#325](https://github.com/Fortran-FOSS-Programmers/ford/issues/325)
- Multi-line strings containing an exclamation mark [\#320](https://github.com/Fortran-FOSS-Programmers/ford/issues/320)
- "Unknown Procedure Type" in call tree [\#319](https://github.com/Fortran-FOSS-Programmers/ford/issues/319)
- Warning: Could not extract source code for proc [\#299](https://github.com/Fortran-FOSS-Programmers/ford/issues/299)
- Exception: Alternate documentation lines can not be inline error [\#295](https://github.com/Fortran-FOSS-Programmers/ford/issues/295)
- Support enums with kind specified for integer literals [\#243](https://github.com/Fortran-FOSS-Programmers/ford/issues/243)

**Merged pull requests:**

- Fix several bugs [\#354](https://github.com/Fortran-FOSS-Programmers/ford/pull/354) ([ZedThree](https://github.com/ZedThree))

## [v6.1.2](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.2) (2021-09-06)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.1.1...v6.1.2)

**Implemented enhancements:**

- Automatic publishing of releases [\#332](https://github.com/Fortran-FOSS-Programmers/ford/issues/332)

**Fixed bugs:**

- jinja2.exceptions.UndefinedError: 'None' has no attribute 'meta' [\#352](https://github.com/Fortran-FOSS-Programmers/ford/issues/352)
- somehow FORD takes number in Format  as subroutine to draw the graph [\#350](https://github.com/Fortran-FOSS-Programmers/ford/issues/350)
- Unclear exception raised [\#292](https://github.com/Fortran-FOSS-Programmers/ford/issues/292)
- Different results with space after '%' character. [\#240](https://github.com/Fortran-FOSS-Programmers/ford/issues/240)

## [v6.1.1](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.1) (2021-07-20)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.1.0...v6.1.1)

## [v6.1.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.1.0) (2021-07-20)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v6.0.0...v6.1.0)

**Implemented enhancements:**

- Switch for ignoring undocumented entities [\#163](https://github.com/Fortran-FOSS-Programmers/ford/issues/163)
- Automatic publishing of releases [\#332](https://github.com/Fortran-FOSS-Programmers/ford/issues/332)

**Fixed bugs:**

- Broken links for the intrinsic modules [\#343](https://github.com/Fortran-FOSS-Programmers/ford/issues/343)
- Submodules lead to a crash - 'FortranModule' object has no attribute 'all\_absinterfaces'  [\#322](https://github.com/Fortran-FOSS-Programmers/ford/issues/322)
- Question: disable sourcecode pages [\#314](https://github.com/Fortran-FOSS-Programmers/ford/issues/314)
- Bad escape crash [\#296](https://github.com/Fortran-FOSS-Programmers/ford/issues/296)
- UnicodeDecodeError [\#270](https://github.com/Fortran-FOSS-Programmers/ford/issues/270)
- ford 5.0.6 crashes on sync images inside module procedure in submodule [\#237](https://github.com/Fortran-FOSS-Programmers/ford/issues/237)

**Closed issues:**

- black? [\#334](https://github.com/Fortran-FOSS-Programmers/ford/issues/334)
- Crash with macro [\#45](https://github.com/Fortran-FOSS-Programmers/ford/issues/45)

**Merged pull requests:**

- Add workflow for publishing to PyPI on release [\#348](https://github.com/Fortran-FOSS-Programmers/ford/pull/348) ([ZedThree](https://github.com/ZedThree))
- Fix flake8 warnings [\#347](https://github.com/Fortran-FOSS-Programmers/ford/pull/347) ([ZedThree](https://github.com/ZedThree))
- Convert setup.py to setup.cfg/pyproject.toml [\#346](https://github.com/Fortran-FOSS-Programmers/ford/pull/346) ([ZedThree](https://github.com/ZedThree))
- Fix and update URLs for intrinsic modules. [\#344](https://github.com/Fortran-FOSS-Programmers/ford/pull/344) ([ZedThree](https://github.com/ZedThree))
- Apply `black` formatting to project; add auto-black to CI [\#342](https://github.com/Fortran-FOSS-Programmers/ford/pull/342) ([ZedThree](https://github.com/ZedThree))
- Linking to external projects [\#338](https://github.com/Fortran-FOSS-Programmers/ford/pull/338) ([haraldkl](https://github.com/haraldkl))
- Use rawstring literals for regexes [\#337](https://github.com/Fortran-FOSS-Programmers/ford/pull/337) ([ZedThree](https://github.com/ZedThree))
- Fix for crash when character default value contains backslash [\#336](https://github.com/Fortran-FOSS-Programmers/ford/pull/336) ([ZedThree](https://github.com/ZedThree))
- Add a few unit tests [\#335](https://github.com/Fortran-FOSS-Programmers/ford/pull/335) ([ZedThree](https://github.com/ZedThree))
- Add support for python -m ford [\#333](https://github.com/Fortran-FOSS-Programmers/ford/pull/333) ([dschwoerer](https://github.com/dschwoerer))
- Warn on missing include files instead of error [\#331](https://github.com/Fortran-FOSS-Programmers/ford/pull/331) ([dschwoerer](https://github.com/dschwoerer))
- Add a trivial regression test [\#330](https://github.com/Fortran-FOSS-Programmers/ford/pull/330) ([ZedThree](https://github.com/ZedThree))
- Allow submodule procedures to have CONTAINS statements [\#321](https://github.com/Fortran-FOSS-Programmers/ford/pull/321) ([pzehner](https://github.com/pzehner))
- Specify order of the subpages in page\_dir [\#318](https://github.com/Fortran-FOSS-Programmers/ford/pull/318) ([ecasglez](https://github.com/ecasglez))
- Do not show the list of source files in index.html if incl\_src is false. [\#316](https://github.com/Fortran-FOSS-Programmers/ford/pull/316) ([ecasglez](https://github.com/ecasglez))
- Change the link to the github repo in the generated html. [\#315](https://github.com/Fortran-FOSS-Programmers/ford/pull/315) ([ecasglez](https://github.com/ecasglez))
- Fix: include files were only processed if the word "include" was lowercase [\#313](https://github.com/Fortran-FOSS-Programmers/ford/pull/313) ([ecasglez](https://github.com/ecasglez))
- Fix missing parentheses on str.lower call [\#311](https://github.com/Fortran-FOSS-Programmers/ford/pull/311) ([ZedThree](https://github.com/ZedThree))
- Fix anchors being hid by navbar for all elements [\#310](https://github.com/Fortran-FOSS-Programmers/ford/pull/310) ([ZedThree](https://github.com/ZedThree))
- Prevent IndexError on single ampersands [\#306](https://github.com/Fortran-FOSS-Programmers/ford/pull/306) ([ajdawson](https://github.com/ajdawson))
- Adding a trivial regression test [\#305](https://github.com/Fortran-FOSS-Programmers/ford/pull/305) ([pclausen](https://github.com/pclausen))
- Added a copy\_subdir option. [\#302](https://github.com/Fortran-FOSS-Programmers/ford/pull/302) ([haraldkl](https://github.com/haraldkl))
- Added the option to define aliases for the documentation by the user. [\#301](https://github.com/Fortran-FOSS-Programmers/ford/pull/301) ([haraldkl](https://github.com/haraldkl))
- fix directory names in error message [\#300](https://github.com/Fortran-FOSS-Programmers/ford/pull/300) ([shoshijak](https://github.com/shoshijak))
- src: Add gitlab as an option [\#297](https://github.com/Fortran-FOSS-Programmers/ford/pull/297) ([HaoZeke](https://github.com/HaoZeke))
- Adding feature to project licenses [\#294](https://github.com/Fortran-FOSS-Programmers/ford/pull/294) ([kevinhng86](https://github.com/kevinhng86))
- Extends now recognised if capitalised [\#289](https://github.com/Fortran-FOSS-Programmers/ford/pull/289) ([oerc0122](https://github.com/oerc0122))
- Fix 267: Inc. all proc doc when missing read more [\#282](https://github.com/Fortran-FOSS-Programmers/ford/pull/282) ([zbeekman](https://github.com/zbeekman))
- Fix \#273: Ensuring `set` is used for module uses data [\#281](https://github.com/Fortran-FOSS-Programmers/ford/pull/281) ([d7919](https://github.com/d7919))
- Only loop over first ten objects in bottom nav links [\#279](https://github.com/Fortran-FOSS-Programmers/ford/pull/279) ([ZedThree](https://github.com/ZedThree))
- Add source code line values to raised exceptions [\#277](https://github.com/Fortran-FOSS-Programmers/ford/pull/277) ([smillerc](https://github.com/smillerc))
- Fixing links in the README files [\#268](https://github.com/Fortran-FOSS-Programmers/ford/pull/268) ([tueda](https://github.com/tueda))
- Add project-file option to hide undocumented elements [\#266](https://github.com/Fortran-FOSS-Programmers/ford/pull/266) ([jhrmnn](https://github.com/jhrmnn))
- Fix invalid "Read more" for components of derived types [\#265](https://github.com/Fortran-FOSS-Programmers/ford/pull/265) ([jhrmnn](https://github.com/jhrmnn))
- Fixed copying MathJax config file [\#264](https://github.com/Fortran-FOSS-Programmers/ford/pull/264) ([cmacmackin](https://github.com/cmacmackin))
- choose encoding and create --force mode [\#263](https://github.com/Fortran-FOSS-Programmers/ford/pull/263) ([narsonalin](https://github.com/narsonalin))
- sourceform: Check for both function calls and sub calls on same line [\#257](https://github.com/Fortran-FOSS-Programmers/ford/pull/257) ([kc9jud](https://github.com/kc9jud))
- recognizing data type: double complex \(issue \#251\) [\#252](https://github.com/Fortran-FOSS-Programmers/ford/pull/252) ([PaulXiCao](https://github.com/PaulXiCao))
- Hide the progress bars when running quietly [\#244](https://github.com/Fortran-FOSS-Programmers/ford/pull/244) ([ibarrass-qmul](https://github.com/ibarrass-qmul))

## [v6.0.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v6.0.0) (2018-06-30)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v5.0.6...v6.0.0)

**Implemented enhancements:**

- Reducing html size [\#205](https://github.com/Fortran-FOSS-Programmers/ford/issues/205)
- Links to routines not included in documentation [\#182](https://github.com/Fortran-FOSS-Programmers/ford/issues/182)
- slow rendering of large graphs [\#176](https://github.com/Fortran-FOSS-Programmers/ford/issues/176)
- Sources always included, is it possible to customize? [\#172](https://github.com/Fortran-FOSS-Programmers/ford/issues/172)

**Fixed bugs:**

- UnicodeDecodeError: 'utf8' codec can't decode byte [\#208](https://github.com/Fortran-FOSS-Programmers/ford/issues/208)
- Incorrect relative path \(project\_url\) in index.html [\#204](https://github.com/Fortran-FOSS-Programmers/ford/issues/204)
- Failure in generating HTML with procedure statement [\#202](https://github.com/Fortran-FOSS-Programmers/ford/issues/202)
- MathJax extension doesn't work with nested/recursive patterns [\#196](https://github.com/Fortran-FOSS-Programmers/ford/issues/196)
- Graph shows calls to module variables [\#190](https://github.com/Fortran-FOSS-Programmers/ford/issues/190)
- Maximum recursion depth with recursive types [\#183](https://github.com/Fortran-FOSS-Programmers/ford/issues/183)
- OOM and RecursionError with large code base [\#174](https://github.com/Fortran-FOSS-Programmers/ford/issues/174)

**Merged pull requests:**

- sources can now be excluded from html output [\#241](https://github.com/Fortran-FOSS-Programmers/ford/pull/241) ([jburgalat](https://github.com/jburgalat))
- Activate graph warnings if any object in the root list has warn true \(\#231\) [\#234](https://github.com/Fortran-FOSS-Programmers/ford/pull/234) ([haraldkl](https://github.com/haraldkl))
- Addressing \#219 [\#220](https://github.com/Fortran-FOSS-Programmers/ford/pull/220) ([haraldkl](https://github.com/haraldkl))
- Re-enable graphs as table and adapt them to changed graph layout. [\#218](https://github.com/Fortran-FOSS-Programmers/ford/pull/218) ([haraldkl](https://github.com/haraldkl))
- added support for specifying lexer of extra\_filetypes [\#217](https://github.com/Fortran-FOSS-Programmers/ford/pull/217) ([cmacmackin](https://github.com/cmacmackin))
- Fix graphlimiting [\#216](https://github.com/Fortran-FOSS-Programmers/ford/pull/216) ([haraldkl](https://github.com/haraldkl))
- Filter empty preprocessor flags; don't treat arithmetic gotos as function references [\#214](https://github.com/Fortran-FOSS-Programmers/ford/pull/214) ([ibarrass-qmul](https://github.com/ibarrass-qmul))
- Be case insensitive when searching for entities which are imported by a use statement. [\#201](https://github.com/Fortran-FOSS-Programmers/ford/pull/201) ([sch1ldkr0ete](https://github.com/sch1ldkr0ete))
- Introduced a maximal graph depth option to limit graph sizes. [\#197](https://github.com/Fortran-FOSS-Programmers/ford/pull/197) ([haraldkl](https://github.com/haraldkl))
- Added an option mathjax\_config for custom setting. [\#195](https://github.com/Fortran-FOSS-Programmers/ford/pull/195) ([mrestelli](https://github.com/mrestelli))
- Skip subdirectories of directories listed in exclude\_dir [\#194](https://github.com/Fortran-FOSS-Programmers/ford/pull/194) ([mrestelli](https://github.com/mrestelli))
- bug: fixed replacements in name conversion [\#192](https://github.com/Fortran-FOSS-Programmers/ford/pull/192) ([zerothi](https://github.com/zerothi))
- enh: reduced memory consumption and speeded up process [\#191](https://github.com/Fortran-FOSS-Programmers/ford/pull/191) ([zerothi](https://github.com/zerothi))
- Fix minor typo in tipuesearch create\_node call [\#186](https://github.com/Fortran-FOSS-Programmers/ford/pull/186) ([d7919](https://github.com/d7919))
- Fix for hidden anchors within pages. [\#178](https://github.com/Fortran-FOSS-Programmers/ford/pull/178) ([sch1ldkr0ete](https://github.com/sch1ldkr0ete))
- Reducing page rendering time [\#175](https://github.com/Fortran-FOSS-Programmers/ford/pull/175) ([sch1ldkr0ete](https://github.com/sch1ldkr0ete))
- Better example [\#169](https://github.com/Fortran-FOSS-Programmers/ford/pull/169) ([zbeekman](https://github.com/zbeekman))

## [v5.0.6](https://github.com/Fortran-FOSS-Programmers/ford/tree/v5.0.6) (2016-09-16)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v5.0.5...v5.0.6)

**Merged pull requests:**

- fixed python3 bug. [\#170](https://github.com/Fortran-FOSS-Programmers/ford/pull/170) ([jacobwilliams](https://github.com/jacobwilliams))

## [v5.0.5](https://github.com/Fortran-FOSS-Programmers/ford/tree/v5.0.5) (2016-09-15)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v5.0.4...v5.0.5)

**Merged pull requests:**

- Update installation documentation for pip install. [\#168](https://github.com/Fortran-FOSS-Programmers/ford/pull/168) ([rouson](https://github.com/rouson))
- Fix base.html to use correct author in the head section. [\#164](https://github.com/Fortran-FOSS-Programmers/ford/pull/164) ([aradi](https://github.com/aradi))

## [v5.0.4](https://github.com/Fortran-FOSS-Programmers/ford/tree/v5.0.4) (2016-07-27)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v5.0.3...v5.0.4)

## [v5.0.3](https://github.com/Fortran-FOSS-Programmers/ford/tree/v5.0.3) (2016-07-27)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v5.0.2...v5.0.3)

## [v5.0.2](https://github.com/Fortran-FOSS-Programmers/ford/tree/v5.0.2) (2016-07-26)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v5.0.1...v5.0.2)

## [v5.0.1](https://github.com/Fortran-FOSS-Programmers/ford/tree/v5.0.1) (2016-07-26)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v5.0.0...v5.0.1)

## [v5.0.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v5.0.0) (2016-07-26)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.6.2...v5.0.0)

## [v4.6.2](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.6.2) (2016-06-11)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.6.1...v4.6.2)

## [v4.6.1](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.6.1) (2016-06-05)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.6.0...v4.6.1)

## [v4.6.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.6.0) (2016-05-15)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.5.4...v4.6.0)

**Merged pull requests:**

- Add homebrew version badge [\#133](https://github.com/Fortran-FOSS-Programmers/ford/pull/133) ([zbeekman](https://github.com/zbeekman))
- Implement customizable preprocessor. [\#129](https://github.com/Fortran-FOSS-Programmers/ford/pull/129) ([aradi](https://github.com/aradi))
- Fix ford not to exit silently when encountering deep paths. [\#127](https://github.com/Fortran-FOSS-Programmers/ford/pull/127) ([aradi](https://github.com/aradi))
- Allow rendering of MathJax in HTTP aswell as HTTPS connections. [\#126](https://github.com/Fortran-FOSS-Programmers/ford/pull/126) ([haraldkl](https://github.com/haraldkl))
- Regex for USE statements now recognizes "use :: module-name". Fixes \#120 [\#123](https://github.com/Fortran-FOSS-Programmers/ford/pull/123) ([sliska314](https://github.com/sliska314))
- Sort page files and directories alphabetically. Fixes \#121 [\#122](https://github.com/Fortran-FOSS-Programmers/ford/pull/122) ([lstagner](https://github.com/lstagner))
- Include the creation date and time in the footer [\#115](https://github.com/Fortran-FOSS-Programmers/ford/pull/115) ([p-vitt](https://github.com/p-vitt))

## [v4.5.4](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.5.4) (2016-03-29)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.5.3...v4.5.4)

## [v4.5.3](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.5.3) (2016-03-27)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.5.2...v4.5.3)

## [v4.5.2](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.5.2) (2016-02-20)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.5.1...v4.5.2)

**Merged pull requests:**

- Fix problem with pypi badge [\#105](https://github.com/Fortran-FOSS-Programmers/ford/pull/105) ([zbeekman](https://github.com/zbeekman))

## [v4.5.1](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.5.1) (2016-01-21)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.5.0...v4.5.1)

**Closed issues:**

- Non-Fortran source files [\#52](https://github.com/Fortran-FOSS-Programmers/ford/issues/52)

**Merged pull requests:**

- Add PyPi and release badges [\#104](https://github.com/Fortran-FOSS-Programmers/ford/pull/104) ([zbeekman](https://github.com/zbeekman))

## [v4.5.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.5.0) (2015-12-23)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.4.0...v4.5.0)

## [v4.4.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.4.0) (2015-11-24)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.3.0...v4.4.0)

## [v4.3.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.3.0) (2015-09-20)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.2.3...v4.3.0)

## [v4.2.3](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.2.3) (2015-08-31)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.2.2...v4.2.3)

## [v4.2.2](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.2.2) (2015-08-30)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.2.1...v4.2.2)

**Merged pull requests:**

- Increase "intrinsic" coverage; allow dummy variables with no intent. [\#80](https://github.com/Fortran-FOSS-Programmers/ford/pull/80) ([pheibarrass](https://github.com/pheibarrass))

## [v4.2.1](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.2.1) (2015-08-26)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.2.0...v4.2.1)

## [v4.2.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.2.0) (2015-08-24)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.1.0...v4.2.0)

## [v4.1.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.1.0) (2015-08-11)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.0.1...v4.1.0)

## [v4.0.1](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.0.1) (2015-07-21)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v4.0.0...v4.0.1)

## [v4.0.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v4.0.0) (2015-07-20)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v3.1.0...v4.0.0)

## [v3.1.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v3.1.0) (2015-07-09)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v3.0.2...v3.1.0)

**Merged pull requests:**

- Zbeekman homebrew patch [\#57](https://github.com/Fortran-FOSS-Programmers/ford/pull/57) ([zbeekman](https://github.com/zbeekman))
- homebrew documentation patch [\#56](https://github.com/Fortran-FOSS-Programmers/ford/pull/56) ([zbeekman](https://github.com/zbeekman))

## [v3.0.2](https://github.com/Fortran-FOSS-Programmers/ford/tree/v3.0.2) (2015-07-02)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v3.0.1...v3.0.2)

## [v3.0.1](https://github.com/Fortran-FOSS-Programmers/ford/tree/v3.0.1) (2015-07-01)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v3.0.0...v3.0.1)

## [v3.0.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v3.0.0) (2015-06-25)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v2.1.0...v3.0.0)

## [v2.1.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v2.1.0) (2015-06-19)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v2.0.0...v2.1.0)

## [v2.0.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v2.0.0) (2015-04-26)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v1.1.0...v2.0.0)

## [v1.1.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v1.1.0) (2015-01-21)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v1.0.1...v1.1.0)

**Merged pull requests:**

- Python 3 compatibility [\#22](https://github.com/Fortran-FOSS-Programmers/ford/pull/22) ([jacobwilliams](https://github.com/jacobwilliams))

## [v1.0.1](https://github.com/Fortran-FOSS-Programmers/ford/tree/v1.0.1) (2015-01-21)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v1.0.2...v1.0.1)

## [v1.0.2](https://github.com/Fortran-FOSS-Programmers/ford/tree/v1.0.2) (2015-01-21)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v1.0.0...v1.0.2)

## [v1.0.0](https://github.com/Fortran-FOSS-Programmers/ford/tree/v1.0.0) (2015-01-19)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v0.5...v1.0.0)

**Fixed bugs:**

- Include syntax conflicts with LaTeX [\#12](https://github.com/Fortran-FOSS-Programmers/ford/issues/12)

**Merged pull requests:**

- Add an option "predocmark" for anticipated doc. [\#18](https://github.com/Fortran-FOSS-Programmers/ford/pull/18) ([mrestelli](https://github.com/mrestelli))

## [v0.5](https://github.com/Fortran-FOSS-Programmers/ford/tree/v0.5) (2015-01-17)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v0.4...v0.5)

**Fixed bugs:**

- Crashes if first line of doc contains a colon [\#11](https://github.com/Fortran-FOSS-Programmers/ford/issues/11)

## [v0.4](https://github.com/Fortran-FOSS-Programmers/ford/tree/v0.4) (2015-01-12)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v0.3...v0.4)

## [v0.3](https://github.com/Fortran-FOSS-Programmers/ford/tree/v0.3) (2015-01-07)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/v0.2...v0.3)

## [v0.2](https://github.com/Fortran-FOSS-Programmers/ford/tree/v0.2) (2015-01-05)

[Full Changelog](https://github.com/Fortran-FOSS-Programmers/ford/compare/48f0ef45a411e4a91950d414c47976dbb810588c...v0.2)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
