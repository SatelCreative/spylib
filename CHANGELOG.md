### Changelog

All notable changes to this project will be documented in this file. Dates are displayed in UTC.

#### [0.10.0](https://github.com/SatelCreative/spylib/compare/0.9.3...0.10.0)
> 13 December 2023

* ⬆️ Upgrade to pydantic 2.5 by @hillairet in https://github.com/SatelCreative/spylib/pull/207


#### [0.9.3](https://github.com/SatelCreative/spylib/compare/0.9.2...0.9.3)
> 13 December 2023

* 📝 Add badges for licence, version, and pypi version to the README by @hillairet in https://github.com/SatelCreative/spylib/pull/209
* ⬆️ Upgrade packages in pyproject.toml by @hillairet in https://github.com/SatelCreative/spylib/pull/210
* 💥 Remove support for python version 3.8, add 3.12 by @hillairet in https://github.com/SatelCreative/spylib/pull/208
* 🐛  Shopify error handling by @lishanl in https://github.com/SatelCreative/spylib/pull/211


#### [0.9.2](https://github.com/SatelCreative/spylib/compare/0.9.1...0.9.2)
> 04 December 2023

* :bug: Handle when the a Shopify API call response body is not a json by @hillairet in https://github.com/SatelCreative/spylib/pull/205


#### [0.9.1](https://github.com/SatelCreative/spylib/compare/0.9.0...0.9.1)
> 08 September 2023
* ⬆️ ➖ Update package dependencies by @lishanl in https://github.com/SatelCreative/spylib/pull/197
* 👷 add python 3.11 to tox test suite by @lishanl in https://github.com/SatelCreative/spylib/pull/198
* 📝 Add token save() and load() examples to admin-api doc by @lishanl in https://github.com/SatelCreative/spylib/pull/199


#### [0.9.0](https://github.com/SatelCreative/spylib/compare/0.8.1...0.9.0)
> 14 July 2022
* 📝  Revise admin api doc by @lishanl in https://github.com/SatelCreative/spylib/pull/184
* :sparkles: Remove default API version and make it manual input by @ponty33 in https://github.com/SatelCreative/spylib/pull/183
* :sparkles: Change load to async by @ponty33 in https://github.com/SatelCreative/spylib/pull/182
* 👷 Add lazydocs validate to CI tests by @lishanl in https://github.com/SatelCreative/spylib/pull/186
* ✨ fastapi webhook hmac validate dependency by @lishanl in https://github.com/SatelCreative/spylib/pull/190
* ♻️ remove package nest-asyncio by @lishanl in https://github.com/SatelCreative/spylib/pull/191
* :alien: 💥  replace app_handle with app_api_key for redirect by @lishanl in https://github.com/SatelCreative/spylib/pull/192
* 🚀 Upgrade tox to v4 by @rahulpatidar0191 in https://github.com/SatelCreative/spylib/pull/195
* :memo: Fix the link to point to the latest docs by @hillairet in https://github.com/SatelCreative/spylib/pull/196

#### [0.8.1](https://github.com/SatelCreative/spylib/compare/0.8.0...0.8.1)
> 14 December 2022
* ✨ Handle GQL non-200 response by @ponty33 in https://github.com/SatelCreative/spylib/pull/155
* 🐛 add 10 seconds leeway for session token check on the nbf by @lishanl in https://github.com/SatelCreative/spylib/pull/175


#### [0.8.0](https://github.com/SatelCreative/spylib/compare/0.7.0...0.8.0)
> 16 September 2022

* 💥🗑️ Remove bonnette specific code by @lishanl in [`#163`](https://github.com/SatelCreative/spylib/pull/163)
* 🐛 Fix fastapi tests by @lishanl in [`#167`](https://github.com/SatelCreative/spylib/pull/167)
* 🎨 add bytes type data support to webhook hmac validate function by @lishanl in [`#168`](https://github.com/SatelCreative/spylib/pull/168)
* ✨ Extract the framework code by @ponty33 in [`#157`](https://github.com/SatelCreative/spylib/pull/157)


#### [0.7.0](https://github.com/SatelCreative/spylib/compare/0.6.0...0.7.0)

> 9 August 2022

* 📝 Add automatically generated release notes by @hillairet in [`#124`](https://github.com/SatelCreative/spylib/pull/124)
* ➕ 🧑‍💻Feature/add markdown link checker by @lishanl in [`#128`](https://github.com/SatelCreative/spylib/pull/128)
* ✨ Add event bridge and pub sub webhook creation  by @lishanl in [`#126`](https://github.com/SatelCreative/spylib/pull/126)
* 🧑‍💻 Brunette => Blue by @qw-in in [`#133`](https://github.com/SatelCreative/spylib/pull/133)
* 👷 fix dependencies reinstallation by @lishanl in [`#134`](https://github.com/SatelCreative/spylib/pull/134)
* ✨ Adding multipass function by @ponty33 in [`#8`](https://github.com/SatelCreative/spylib/pull/8)
* 👽️ 🔥 Fix/remove jwt by @lishanl in [`#137`](https://github.com/SatelCreative/spylib/pull/137)
* ♻️ Fix/decouple fastapi by @lishanl in [`#139`](https://github.com/SatelCreative/spylib/pull/139)
* 🔒️ remove sensitive data from error log by @lishanl in [`#141`](https://github.com/SatelCreative/spylib/pull/141)
* ♻️💥 Fix/reorganize modules by @lishanl in [`#142`](https://github.com/SatelCreative/spylib/pull/142)
* ✨💥 [oauth] add exchange_token by @qw-in in [`#146`](https://github.com/SatelCreative/spylib/pull/146)
* ♻️💥 Fix/extract webhooks functions by @lishanl in [`#143`](https://github.com/SatelCreative/spylib/pull/143)
* ✨ [oauth] Add oauth hmac signature validation function by @qw-in in [`#147`](https://github.com/SatelCreative/spylib/pull/147)
* 🐛  Fix webhook graphql queries not found by @lishanl in [`#151`](https://github.com/SatelCreative/spylib/pull/151)
* ✨ Document versioning  by @ponty33 in [`#153`](https://github.com/SatelCreative/spylib/pull/153)
* ♻️ Fix/remove duplicated token models by @lishanl in [`#154`](https://github.com/SatelCreative/spylib/pull/154)
* 🐛 Deprecate abstractclassmethod by @ponty33 in [`#156`](https://github.com/SatelCreative/spylib/pull/156)
* 📝 Add GitHub autogenerated release notes to releasing by @hillairet in [`#160`](https://github.com/SatelCreative/spylib/pull/160)
* ✨ Add new pr-title-checker by @rahulpatidar0191 in [`#161`](https://github.com/SatelCreative/spylib/pull/161)

#### [0.6.0](https://github.com/SatelCreative/satel-spylib/compare/0.5.0...0.6.0)

> 27 April 2022

- 📝 add webhook doc [`#121`](https://github.com/SatelCreative/satel-spylib/pull/121)
- 📝 Docs/syntax highlighting [`#122`](https://github.com/SatelCreative/satel-spylib/pull/122)
- update mkdocs to the latest [`#120`](https://github.com/SatelCreative/satel-spylib/pull/120)
- ✨ 💥 Feature/webhook verification [`#113`](https://github.com/SatelCreative/satel-spylib/pull/113)
- ✨ Feature/webhook create [`#112`](https://github.com/SatelCreative/satel-spylib/pull/112)
- 🐛 Fix/Shopify graphql error not surfacing [`#106`](https://github.com/SatelCreative/satel-spylib/pull/106)
- ✨ Enforce gitmoji in PR title [`#108`](https://github.com/SatelCreative/satel-spylib/pull/108)
- Fix/replace shortuuid dependency with code [`#104`](https://github.com/SatelCreative/satel-spylib/pull/104)
- remove loguru and replace with the standard logging [`#103`](https://github.com/SatelCreative/satel-spylib/pull/103)
- Make fastapi optional and raise error when imported but not installed [`#101`](https://github.com/SatelCreative/satel-spylib/pull/101)
- add change log [`dc303dd`](https://github.com/SatelCreative/satel-spylib/commit/dc303dd9f117b4f4aeaf7b2c68300e5dd6ed670b)
- update spylib version [`aad872a`](https://github.com/SatelCreative/satel-spylib/commit/aad872a46d33dea7a4772b74699362e8d4771cdb)

#### [0.5.0](https://github.com/SatelCreative/satel-spylib/compare/0.4...0.5.0)

> 15 March 2022

- Release/0.5.0 [`#102`](https://github.com/SatelCreative/satel-spylib/pull/102)
- Add path_prefix param to init oauth router and url [`#82`](https://github.com/SatelCreative/satel-spylib/pull/82)
- :bug: Fix tests to prevent pytest from hanging [`#98`](https://github.com/SatelCreative/satel-spylib/pull/98)
- Miscellaneous documentation improvements [`#99`](https://github.com/SatelCreative/satel-spylib/pull/99)
- Merge config files, add brunette, add .vscode [`#95`](https://github.com/SatelCreative/satel-spylib/pull/95)
- Fix/dependency versions [`#85`](https://github.com/SatelCreative/satel-spylib/pull/85)
- 📝 Reorganize the documentation in sections [`#88`](https://github.com/SatelCreative/satel-spylib/pull/88)
- Update Shopify API [`#81`](https://github.com/SatelCreative/satel-spylib/pull/81)
- Add 3.8 and 3.10 to tests [`#79`](https://github.com/SatelCreative/satel-spylib/pull/79)
- Fix session token format [`#76`](https://github.com/SatelCreative/satel-spylib/pull/76)

#### [0.4](https://github.com/SatelCreative/satel-spylib/compare/0.3.3...0.4)

> 7 December 2021

- Release/0.4 [`#73`](https://github.com/SatelCreative/satel-spylib/pull/73)
- Use only poetry to publish as it should be. [`#69`](https://github.com/SatelCreative/satel-spylib/pull/69)
- Updated docs index.md [`#72`](https://github.com/SatelCreative/satel-spylib/pull/72)
- Added gh action to compare files [`#65`](https://github.com/SatelCreative/satel-spylib/pull/65)
- Added HMAC tests [`#63`](https://github.com/SatelCreative/satel-spylib/pull/63)
- Added implementation of private token [`#64`](https://github.com/SatelCreative/satel-spylib/pull/64)
- Added mkdocs and lazydocs [`#56`](https://github.com/SatelCreative/satel-spylib/pull/56)
- Feature/add flake8 quotes [`#59`](https://github.com/SatelCreative/satel-spylib/pull/59)
- Status code / request constants  [`#40`](https://github.com/SatelCreative/satel-spylib/pull/40)
- Added in validator [`#48`](https://github.com/SatelCreative/satel-spylib/pull/48)
- Remove environment variables [`#45`](https://github.com/SatelCreative/satel-spylib/pull/45)
- Feature/session tokens [`#26`](https://github.com/SatelCreative/satel-spylib/pull/26)
- Feature/add automated testing [`#39`](https://github.com/SatelCreative/satel-spylib/pull/39)
- Docs/howto publish [`#38`](https://github.com/SatelCreative/satel-spylib/pull/38)
- Add release review process to publication section [`9731d58`](https://github.com/SatelCreative/satel-spylib/commit/9731d58a77092b7d717f06911775d24a05f2536f)
- Add Nathan as codeowner [`4442a94`](https://github.com/SatelCreative/satel-spylib/commit/4442a943bd8d128f452794c5695a0da079cadb61)
- Add back accidentally deleted build-backend line [`3ce451c`](https://github.com/SatelCreative/satel-spylib/commit/3ce451c6cb77321cb394e921fe7a36bc4c318641)

#### [0.3.3](https://github.com/SatelCreative/satel-spylib/compare/0.3...0.3.3)

> 3 December 2021

- Switch to 0.3.3 plus remove flit [`6c8e8af`](https://github.com/SatelCreative/satel-spylib/commit/6c8e8af8b858415af1e441d414ed987dbf8e9bda)
- Switch to version 0.3.2 just to publish to pypi [`52ab28d`](https://github.com/SatelCreative/satel-spylib/commit/52ab28dcac0c32041ce61de6a6a8d0d42c537a57)
- Switch to version 0.3.1 [`e9fcfa9`](https://github.com/SatelCreative/satel-spylib/commit/e9fcfa9590812530c73109bc357ec6930b2244ec)

#### [0.3](https://github.com/SatelCreative/satel-spylib/compare/0.2.2...0.3)

> 10 November 2021

- Feature/token refactor [`#23`](https://github.com/SatelCreative/satel-spylib/pull/23)
- Altered test folder structure [`#17`](https://github.com/SatelCreative/satel-spylib/pull/17)
- Credit rate limit for GraphQL [`#14`](https://github.com/SatelCreative/satel-spylib/pull/14)
- Add operation name for GraphQL [`#13`](https://github.com/SatelCreative/satel-spylib/pull/13)
- Change version to 0.3 [`6b9b436`](https://github.com/SatelCreative/satel-spylib/commit/6b9b436467fbf81da9fcc4f25bd603f12b0085d6)

#### [0.2.2](https://github.com/SatelCreative/satel-spylib/compare/0.2.1...0.2.2)

> 22 September 2021

- use callback_path variable in the redirect url [`#10`](https://github.com/SatelCreative/satel-spylib/pull/10)
- Prep for release 0.2.2 [`87c6d72`](https://github.com/SatelCreative/satel-spylib/commit/87c6d7220ce29c8092cbea849bf2156b642b44b5)

#### [0.2.1](https://github.com/SatelCreative/satel-spylib/compare/0.1...0.2.1)

> 29 June 2021

- Add py.typed to ship typing hint [`#7`](https://github.com/SatelCreative/satel-spylib/pull/7)
- Add rate limit handling to gql call [`#5`](https://github.com/SatelCreative/satel-spylib/pull/5)
- aclose [`#6`](https://github.com/SatelCreative/satel-spylib/pull/6)
- add rate limit handling for gql call [`e7c7fd3`](https://github.com/SatelCreative/satel-spylib/commit/e7c7fd33c8eb597f5e2f30812f907c491687dfcd)
- Add flit and set config for it [`b0383eb`](https://github.com/SatelCreative/satel-spylib/commit/b0383ebeb0b13b07b67e57dc6cb81df85d42aba9)
- Add version and description for flit [`ad31a90`](https://github.com/SatelCreative/satel-spylib/commit/ad31a90b1c5816ca1b81d1e4b6d64fb51688ecd9)

#### 0.1

> 17 June 2021

- Feature/more store rest tests [`#3`](https://github.com/SatelCreative/satel-spylib/pull/3)
- Docs/first readme [`#1`](https://github.com/SatelCreative/satel-spylib/pull/1)
- Add first version with tests passing [`27e5f8d`](https://github.com/SatelCreative/satel-spylib/commit/27e5f8d6997a022f41153ff68433532a1cddd372)
- Initialize project using poetry [`8ce2e71`](https://github.com/SatelCreative/satel-spylib/commit/8ce2e71d7ba7601efedd7769942ec49865409905)
- Add more development packages [`9882953`](https://github.com/SatelCreative/satel-spylib/commit/98829538fea14ffe62bcb6ac716b9879a1a14cbf)
