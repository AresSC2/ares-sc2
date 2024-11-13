# Changelog

<!--next-version-placeholder-->

## v2.27.3 (2024-11-13)

### Fix

* Prevent 3x3 too close to existing T wall ([`bad58b1`](https://github.com/AresSC2/ares-sc2/commit/bad58b1cb35914b1434952951ade1b56d6268500))

## v2.27.2 (2024-11-02)

### Fix

* Restore power can repower at wall properly ([`cff0fb9`](https://github.com/AresSC2/ares-sc2/commit/cff0fb949a79a62014bbae2323ce5b60552260a7))

## v2.27.1 (2024-10-20)

### Fix

* Check for alternative warpgate structure ([`0a3c442`](https://github.com/AresSC2/ares-sc2/commit/0a3c44227318d3bfdb476e8239cd020b862a4c40))

## v2.27.0 (2024-10-17)

### Feature

* New upgrade controller ([`36cbbf5`](https://github.com/AresSC2/ares-sc2/commit/36cbbf5e054889d937ed8c8e56e3b412fa609a8e))
* Refactor teching up into a seperate behavior ([`17f109c`](https://github.com/AresSC2/ares-sc2/commit/17f109cfc4e55e4b7e63af652a229d3b0bcc45b6))

## v2.26.0 (2024-09-29)

### Feature

* Build runner allows switching openings on the fly ([`d1939bb`](https://github.com/AresSC2/ares-sc2/commit/d1939bb833e07a128cce92129fe62696bf65ad19))

### Documentation

* Add a section on switching openings during game ([`540bd54`](https://github.com/AresSC2/ares-sc2/commit/540bd546dba82c5b2da5c02b9388999292e14f62))

## v2.25.5 (2024-09-20)

### Fix

* Crash on keeping worker safe ([`19ca95c`](https://github.com/AresSC2/ares-sc2/commit/19ca95ce2cafb8dc8f8d0e7718b8626362d5aefd))

## v2.25.4 (2024-09-20)

### Fix

* Prevent transforming warpgates blocking build runner ([`335bcbe`](https://github.com/AresSC2/ares-sc2/commit/335bcbe00397ab2a88896c6300dc67f92f58049e))

## v2.25.3 (2024-09-17)

### Fix

* Widen coridoor between 3x3 structures ([`04cf455`](https://github.com/AresSC2/ares-sc2/commit/04cf455b953d9c70dc4ec5e8611198ad89eb593a))

## v2.25.2 (2024-09-16)

### Fix

* Add T corridoor to help prevent wall off ([`499587e`](https://github.com/AresSC2/ares-sc2/commit/499587ea1d1f5437496dedb0f7eaf2c7cf5f3acb))

## v2.25.1 (2024-09-16)

### Fix

* Worker return resource only if worker exists ([`d6ae746`](https://github.com/AresSC2/ares-sc2/commit/d6ae746475a1e9d6df0c7359ff4cffced0ba8ca1))

## v2.25.0 (2024-09-16)

### Feature

* Dont add proportion production if idle build structures exist ([`09eefe1`](https://github.com/AresSC2/ares-sc2/commit/09eefe196229f7db2b28819865bf84ad70f6ad9a))

### Fix

* Add gaps in building formation to prevent some wall off scenarios ([`752d468`](https://github.com/AresSC2/ares-sc2/commit/752d468484dc5dde02b0e3373a06b7c7ef5941be))
* Get scout and building workers to return resources ([`48275cc`](https://github.com/AresSC2/ares-sc2/commit/48275cc3cfee073c6b8a955346648cce9e0d0be7))

## v2.24.0 (2024-09-15)

### Feature

* Production controller rewrite ([`b719e97`](https://github.com/AresSC2/ares-sc2/commit/b719e97cce7d6b1f0e7747eb75988081f6e254c7))

## v2.23.0 (2024-09-13)

### Feature

* Add expansion controller behavior ([`2da913a`](https://github.com/AresSC2/ares-sc2/commit/2da913a521f650e67db72c509753da33565cd16a))

## v2.22.0 (2024-09-08)

### Feature

* Add build workers behavior ([`be24cbf`](https://github.com/AresSC2/ares-sc2/commit/be24cbf64d081f2e195d697529fa56aaecf8cf79))
* Add gas building controller ([`727650a`](https://github.com/AresSC2/ares-sc2/commit/727650aaab53df0fee4fd7b2e680ab22fdb0cffb))

### Fix

* Circular import ([`bf2fc66`](https://github.com/AresSC2/ares-sc2/commit/bf2fc66dfccabe463f481d02bccb9788ea600088))
* Add missing tech requirement structures ([`c6aeb1c`](https://github.com/AresSC2/ares-sc2/commit/c6aeb1c7eea2d52979d96635688c3b21e1797efc))

### Documentation

* Add api reference for new behaviors ([`bdba0fe`](https://github.com/AresSC2/ares-sc2/commit/bdba0fe42ee51df0e9a0b50a81c137a236b3d1bf))

## v2.21.2 (2024-09-03)

### Fix

* Check for warpgate presence when teching up in ProductionController ([`2e56ef1`](https://github.com/AresSC2/ares-sc2/commit/2e56ef11f8ebd3b9cbfa167592378918b736d6c6))

## v2.21.1 (2024-09-03)

### Fix

* Remove unneeded logic that was modifying structures_dict for no reason ([`3a9ad82`](https://github.com/AresSC2/ares-sc2/commit/3a9ad8282f88eb2074fd7498369779d29875e0eb))
* Prevent build runner incorrectly ending step ([`9da0284`](https://github.com/AresSC2/ares-sc2/commit/9da02848023782c5f50cfb50f11d40af0a0c4d23))
* Teching up can be reached if build structures are present ([`d94bb5e`](https://github.com/AresSC2/ares-sc2/commit/d94bb5ea8f3efb2f7d9faa5cfc199de5d09918da))

## v2.21.0 (2024-09-02)

### Feature

* Improved placement layout of protoss main wall ([`9b5f6ac`](https://github.com/AresSC2/ares-sc2/commit/9b5f6ac98315109f6cf9193ba49c17bb582c5fa9))

### Fix

* UseAbility behavior returns False if ability not possible ([`95d4ee7`](https://github.com/AresSC2/ares-sc2/commit/95d4ee7055ef2d22e25150bdb423e802ab6d244d))

## v2.20.6 (2024-08-26)

### Fix

* Prevent over producing production for low proportion units ([`5df3685`](https://github.com/AresSC2/ares-sc2/commit/5df368524236fe800868b7c6a5b110354077c172))
* Probes factor in shields when fleeing ([`5116422`](https://github.com/AresSC2/ares-sc2/commit/51164228504df8713f2ff31de8b20d43fc09f37b))

## v2.20.5 (2024-08-22)

### Fix

* Old building workers get a gather command when reassigned ([`ee93896`](https://github.com/AresSC2/ares-sc2/commit/ee938962ead79031b3b3e7fa20f6c23e734a5863))

### Documentation

* Chat debug and influence tutorials ([`033bd9f`](https://github.com/AresSC2/ares-sc2/commit/033bd9f459310299ec4b276c8bb8ab6d2501a3fb))
* New gotchas tutorial, replaces tips and tricks ([`a64810e`](https://github.com/AresSC2/ares-sc2/commit/a64810e562649ed6e2c6e9550268167831fe8440))

## v2.20.4 (2024-08-07)

### Fix

* Imports in test bots ([`24ac400`](https://github.com/AresSC2/ares-sc2/commit/24ac40033678b51b9de33402ffd8733f7340c4ae))

## v2.20.3 (2024-07-30)

### Fix

* Prevent intel manager running on arcade mode ([`27c428c`](https://github.com/AresSC2/ares-sc2/commit/27c428ccfa380ac45a5b02262dd4172503cbb3df))

## v2.20.2 (2024-07-24)

### Fix

* Ensure teching up works as expected in ProductionController ([`5525d0f`](https://github.com/AresSC2/ares-sc2/commit/5525d0fc48115fe7edd4ee523ad9fc830cfe4906))
* Check warpgate when considering if gateways are present ([`5cb545d`](https://github.com/AresSC2/ares-sc2/commit/5cb545d12b52d84af8b0674e3bef182a38bc0af8))

## v2.20.1 (2024-07-22)

### Fix

* Allow building logic to be reached ([`4801734`](https://github.com/AresSC2/ares-sc2/commit/48017346ee71930414f217cafe22fd1c1f4b8368))

## v2.20.0 (2024-07-22)

### Feature

* Add min shield perc arg to select worker ([`7946fbf`](https://github.com/AresSC2/ares-sc2/commit/7946fbfbbb7a976eae4f883a9631ec3798e960a1))

### Fix

* Temp fix for probe sometimes not building gas ([`d6b7337`](https://github.com/AresSC2/ares-sc2/commit/d6b73370a303c04d18d09eaed4c410aec688824f))

## v2.19.2 (2024-07-21)

### Fix

* Refactor find pylon placement to prevent crash ([`5d62c47`](https://github.com/AresSC2/ares-sc2/commit/5d62c47c48025cf00a1c6b6c1a7cefd8de01dc13))

## v2.19.1 (2024-07-20)

### Fix

* Circular import ([`ae855d8`](https://github.com/AresSC2/ares-sc2/commit/ae855d8480616b5d121d35c96bc249de9a43ae6d))

## v2.19.0 (2024-07-20)

### Feature

* Add RestorePower behavior ([`465a67a`](https://github.com/AresSC2/ares-sc2/commit/465a67a511468c87623a8db21759416bc182a26d))

### Documentation

* Add macro plan example to tutorial ([`9449aef`](https://github.com/AresSC2/ares-sc2/commit/9449aef2e132d45c24bccf437c6182bd26ba413c))

## v2.18.1 (2024-07-16)

### Fix

* Rename local variable so prod pylons get found ([`2b646d0`](https://github.com/AresSC2/ares-sc2/commit/2b646d0a9139b9d48f69baaf02b18533ba59f7be))
* Increase y stride on extra 2x2 to prevent blockages ([`05dce96`](https://github.com/AresSC2/ares-sc2/commit/05dce960a5b69a51703d52d5934433d78da9cb9d))
* Prevent build runner calling placement query unnecessary ([`bce45cf`](https://github.com/AresSC2/ares-sc2/commit/bce45cfb08d411d2d16d56c632cc7db1f4a4d6a6))

## v2.18.0 (2024-07-14)

### Feature

* Add intel manager with mediator access ([`68ec246`](https://github.com/AresSC2/ares-sc2/commit/68ec24640ca35bc6f06defcdac9cff16c372e060))

## v2.17.0 (2024-07-12)

### Feature

* Improve premoving build probe timing ([`2ebdc14`](https://github.com/AresSC2/ares-sc2/commit/2ebdc14cdd96fe3ca1213e62d2e9fed4366b13bf))

## v2.16.2 (2024-07-06)

### Fix

* Prevent production controller from trying to build warpgate ([`e696364`](https://github.com/AresSC2/ares-sc2/commit/e696364d65237b0e9e239de0ccf57d615593f987))

## v2.16.1 (2024-07-06)

### Fix

* Update main squad attribute correctly ([`a649a2b`](https://github.com/AresSC2/ares-sc2/commit/a649a2b827638f7c18b64c0c927231f9af5ed9be))

## v2.16.0 (2024-07-05)

### Feature

* Spawn controller allows gateways to morph ([`d98c394`](https://github.com/AresSC2/ares-sc2/commit/d98c394269d44c406f1dcdc5080577eb3c02edad))

### Fix

* Attempt to prevent artosis pylon ([`f6a38ea`](https://github.com/AresSC2/ares-sc2/commit/f6a38ea738547e6bf2514ca1028b017de42b0b77))

## v2.15.1 (2024-07-04)

### Fix

* Better handling of target types in _give_units_same_order ([`f6d00a7`](https://github.com/AresSC2/ares-sc2/commit/f6d00a7e5ef25b96a8954d58e50b6204af477fa6))

## v2.15.0 (2024-06-29)

### Feature

* Support archons in spawn controller and build runner ([`0f1bbab`](https://github.com/AresSC2/ares-sc2/commit/0f1bbabd974ae3ee5ebe15ed131bc1902dcffc8a))

### Documentation

* Add some warnings about morphing units from other units ([`503d376`](https://github.com/AresSC2/ares-sc2/commit/503d3762ef4c251c7b040cab9af2c25572c7413b))

## v2.14.4 (2024-06-17)

### Fix

* Check for all buildable plate types ([`9ffdfdb`](https://github.com/AresSC2/ares-sc2/commit/9ffdfdbdec40d1459abc92312244016832887727))

## v2.14.3 (2024-06-13)

### Fix

* Add unbuildable plates to avoid grid when generating placements ([`d98c5e4`](https://github.com/AresSC2/ares-sc2/commit/d98c5e4460ac195f6cdb9c979e651db9128acbce))

## v2.14.2 (2024-06-12)

### Fix

* Search pylons at alternative bases for placement ([`437cab8`](https://github.com/AresSC2/ares-sc2/commit/437cab86c87b35a2b41d6d63881cca729f9f89cc))

## v2.14.1 (2024-06-09)

### Fix

* Add missing import in init file ([`145446c`](https://github.com/AresSC2/ares-sc2/commit/145446cc8b0cd2f61ae3a65e2b0e29cb108f6c78))

## v2.14.0 (2024-06-09)

### Feature

* New group use ability behavior ([`23b0e6b`](https://github.com/AresSC2/ares-sc2/commit/23b0e6b37092a10a3e555dbd6dc2b72c9bd88cb2))

## v2.13.1 (2024-06-02)

### Fix

* Out of map bounds ([`521c363`](https://github.com/AresSC2/ares-sc2/commit/521c3635504cdeebf73f57a3fe6add7f1b5542c7))

## v2.13.0 (2024-06-02)

### Feature

* Improve retreat position for stutter back group ([`f4b1fea`](https://github.com/AresSC2/ares-sc2/commit/f4b1fea44fb3d1cb708697eedddfd142f232205a))

## v2.12.3 (2024-06-01)

### Fix

* Only use completed ths for chrono ([`83ac1c4`](https://github.com/AresSC2/ares-sc2/commit/83ac1c42fa7355c2c6a92e5ca87d66425f09d8f9))

## v2.12.2 (2024-06-01)

### Fix

* Ramp target in build runner builds in main ([`3b75a97`](https://github.com/AresSC2/ares-sc2/commit/3b75a97fea11a1d2160e652144b98ccc343c1333))

## v2.12.1 (2024-06-01)

### Fix

* Run game placement query to ensure warpin placement ([`da8e706`](https://github.com/AresSC2/ares-sc2/commit/da8e706a90a5427abf008dddeaa319257f6c0ae5))

## v2.12.0 (2024-06-01)

### Feature

* Find initial optimal pylon to build around ([`175954f`](https://github.com/AresSC2/ares-sc2/commit/175954f34f5eb5e5028573dc1ff72aa074a95706))
* Core shortcut command works for chrono ([`abf3c40`](https://github.com/AresSC2/ares-sc2/commit/abf3c402fa17a46803f30580cd5b3126a992bec5))
* Allow structure build order commands at target options ([`e16933f`](https://github.com/AresSC2/ares-sc2/commit/e16933f5a8d4d27dab85cf86950f3515747493b2))

### Fix

* Prevent crash completing steps out of index ([`85a01f7`](https://github.com/AresSC2/ares-sc2/commit/85a01f79abf3ea72e68b96e5ef0adeca5a90552e))

## v2.11.1 (2024-05-31)

### Fix

* Build runner detects structure steps have started correctly ([`8d0199b`](https://github.com/AresSC2/ares-sc2/commit/8d0199b9c7ad7c747d4eebcfde6ede078e110df2))
* Tech requirement for immortal ([`5a32601`](https://github.com/AresSC2/ares-sc2/commit/5a32601a3a632db1d14a45ade4efd50ea2417418))

### Documentation

* Add to build runner tutorial ([`331d04f`](https://github.com/AresSC2/ares-sc2/commit/331d04fb8dd79ede746407a3865f07d9664884e6))

## v2.11.0 (2024-05-29)

### Feature

* Build runner supports scout and duplicate commands ([`c8d939d`](https://github.com/AresSC2/ares-sc2/commit/c8d939d2200f34183d92d0c5ad32147591af2540))
* Build runner supports autosupply option ([`a444760`](https://github.com/AresSC2/ares-sc2/commit/a44476038716593e8d76a8e089f8051ff19fa130))

### Documentation

* Extend build runner tutorial with new features ([`a7b7017`](https://github.com/AresSC2/ares-sc2/commit/a7b70173823c7ea7495d0005b8930fdda61aafb3))

## v2.10.1 (2024-05-28)

### Fix

* Ensure both Point2 and Unit work for group targets ([`d26778a`](https://github.com/AresSC2/ares-sc2/commit/d26778ab0b9f5f63f51a8ed5599f00e587f20650))

## v2.10.0 (2024-05-28)

### Feature

* Improve stutter group back behavior ([`0e84b41`](https://github.com/AresSC2/ares-sc2/commit/0e84b4178fc3ac4cadce87f1ea1e492ec8ac7854))

### Fix

* Stutter group back works with Unit object target ([`6cfe19e`](https://github.com/AresSC2/ares-sc2/commit/6cfe19e6630497d86bee300f512c6c2b5b63cef2))

## v2.9.0 (2024-05-25)

### Feature

* Build runner allows spawning of units by target ([`cecfbeb`](https://github.com/AresSC2/ares-sc2/commit/cecfbeb2255dfce297fe8cda5a50952677d40b13))
* SpawnController supports warp ins ([`374e740`](https://github.com/AresSC2/ares-sc2/commit/374e74012e43f0c328e1647c6c39744d7e6aa90c))
* Simulate warpin query and find placements ([`2551a04`](https://github.com/AresSC2/ares-sc2/commit/2551a04f36595e4de2629235d475cfb8e93430d8))

### Documentation

* Update build runner docs with new target options ([`373b67b`](https://github.com/AresSC2/ares-sc2/commit/373b67b86e0ac39651ff19d360fef7567907e5ab))

## v2.8.0 (2024-05-20)

### Feature

* Build runner supports upgrades ([`a80e3c9`](https://github.com/AresSC2/ares-sc2/commit/a80e3c95e5e2602b43a93f5619788a818e119431))
* Support core and gate strings as build step commands ([`d0f8371`](https://github.com/AresSC2/ares-sc2/commit/d0f83716130005df1419b27950e8f29178b07b14))

### Documentation

* Add additional build runner info ([`f3bb82f`](https://github.com/AresSC2/ares-sc2/commit/f3bb82f7b0ec8c5056c270cd0249095c66268eb4))

## v2.7.4 (2024-05-18)

### Fix

* Add missing enemy influence to ground to air grid ([`24b21e7`](https://github.com/AresSC2/ares-sc2/commit/24b21e72b9576c9a6f81cd46a5b78fce34805c98))

## v2.7.3 (2024-05-04)

### Fix

* Remove workers from expired gas buildings ([`5971c30`](https://github.com/AresSC2/ares-sc2/commit/5971c3099220adf90fd4fe5c3e2b47e6c3954ec4))
* Remove stuck scvs / remove workers with duplicate positions ([`53667c2`](https://github.com/AresSC2/ares-sc2/commit/53667c296b038e63ff6f0bd2e78f1e4b4e4d4a3a))

## v2.7.2 (2024-04-23)

### Fix

* Remove worker from mining properly ([`cd002c0`](https://github.com/AresSC2/ares-sc2/commit/cd002c097242d8b29cc767f7266af4f038ea2c0f))

## v2.7.1 (2024-04-20)

### Fix

* Ensure target has value in building tracker ([`a6227dd`](https://github.com/AresSC2/ares-sc2/commit/a6227ddc41ff134fe04ba09146bb77cb47e9f8cb))

## v2.7.0 (2024-04-17)

### Feature

* Cancel stucture mediator call ([`c8c7357`](https://github.com/AresSC2/ares-sc2/commit/c8c7357e0a4093d572786b76cce12aaa0246eb4e))

### Documentation

* Add initial group maneuver tutorial ([`ba183f9`](https://github.com/AresSC2/ares-sc2/commit/ba183f9249cd0bf8be20488a0a6888dcaeed2e3f))

## v2.6.2 (2024-04-15)

### Fix

* New scv may resume building gas ([`242bcfd`](https://github.com/AresSC2/ares-sc2/commit/242bcfd2b4ab9f5b4bca597e5708f5854d4b0d7b))

## v2.6.1 (2024-04-10)

### Fix

* Prevent changeling influence being added ([`25566b3`](https://github.com/AresSC2/ares-sc2/commit/25566b35b3d8f239f071a0573b93be1377d9ae15))

## v2.6.0 (2024-03-31)

### Feature

* Natural bunker placement ([`60873f2`](https://github.com/AresSC2/ares-sc2/commit/60873f28453f9de9f7906e4a0dcbec97ac7b2b0c))

## v2.5.1 (2024-03-30)

### Fix

* Overproduce on low tech behaves as expected ([`4eb78c1`](https://github.com/AresSC2/ares-sc2/commit/4eb78c1367fb1fc517188331df3bb9bd690c4d26))

## v2.5.0 (2024-03-21)

### Feature

* Only select persistent worker generically ([`afa60d3`](https://github.com/AresSC2/ares-sc2/commit/afa60d36b4b2879595a76a7595d3489af144ee84))

## v2.4.3 (2024-03-19)

### Fix

* Zerg morphs work correctly in spawn controller ([`f3bfb58`](https://github.com/AresSC2/ares-sc2/commit/f3bfb58a0a75be4b2ac18e535ff915046bb65f76))

## v2.4.2 (2024-03-19)

### Fix

* Reuse SpawnController in build runner to enable build from reactors ([`d70dd70`](https://github.com/AresSC2/ares-sc2/commit/d70dd701e6861aae87bef155d2b86e570cc0fed4))
* Correctly retrieve build from structures ([`2553a7a`](https://github.com/AresSC2/ares-sc2/commit/2553a7a905ffcbf9fa3d465ad5d59b0f5cb22b5e))

## v2.4.1 (2024-03-17)

### Fix

* Building tracker check for any structure build progress ([`0452e1d`](https://github.com/AresSC2/ares-sc2/commit/0452e1d53330230ca62128943c0dfd0842ce594e))

## v2.4.0 (2024-03-14)

### Feature

* Update cython to get find center mass ([`05214bb`](https://github.com/AresSC2/ares-sc2/commit/05214bb9cfdea1e64deb57d1a7be0de266073036))

## v2.3.0 (2024-03-12)

### Feature

* Stutter forward enemy units argument ([`80ec1d4`](https://github.com/AresSC2/ares-sc2/commit/80ec1d4834235eab501dec71c82c1c189a258ef3))
* Build order ramp position moved if close enemy ([`7d083eb`](https://github.com/AresSC2/ares-sc2/commit/7d083eb8cabeb60d5e63b689b8fc73fd372f8814))

### Fix

* Stutter group back duplicate order check ([`d468066`](https://github.com/AresSC2/ares-sc2/commit/d468066f1b97f445c3e7f7381188b6cc7ac04b63))

## v2.2.2 (2024-03-04)

### Fix

* Ensure unit tags are cleaned up from deleted squads ([`d39cb69`](https://github.com/AresSC2/ares-sc2/commit/d39cb69cebba0c09cb03f5fb7f42fcd9a93d0204))
* Keep group safe only returns true if action issued ([`f2c6752`](https://github.com/AresSC2/ares-sc2/commit/f2c675279a56f3631dcfc7428aacf73176f48759))

### Performance

* Only retrieve unassigned_workers if available_minerals ([`9196360`](https://github.com/AresSC2/ares-sc2/commit/9196360754c69a5ce37caa98293ee21836d7304b))

## v2.2.1 (2024-03-04)

### Fix

* Remove unit tag from squads when assigning new role ([`aa2d20d`](https://github.com/AresSC2/ares-sc2/commit/aa2d20dd096d5b60ee353fafde149f9ebd9f7988))

## v2.2.0 (2024-02-27)

### Feature

* Request to remove unit from squads ([`732e462`](https://github.com/AresSC2/ares-sc2/commit/732e462d570d48be0fdfecb3f493b04fcc1fef39))

## v2.1.1 (2024-02-23)

### Fix

* Assign persistent worker earlier ([`2ba0414`](https://github.com/AresSC2/ares-sc2/commit/2ba04142fc90905a30a40d4246497aa5438d710f))

### Documentation

* Add migration tutorial ([`52e867e`](https://github.com/AresSC2/ares-sc2/commit/52e867ee55423ade4612161107d845b9c04ca919))

## v2.1.0 (2024-02-21)

### Feature

* Add ground to air grid with influence ([`79136d5`](https://github.com/AresSC2/ares-sc2/commit/79136d5d524243a9647d21459339e61c5b55706e))

## v2.0.2 (2024-02-20)

### Fix

* Links in docs ([`f68a480`](https://github.com/AresSC2/ares-sc2/commit/f68a4804d2972decac315d174e832d4fcee87d5f))

### Documentation

* Improve docstrings throughout ([`c11df7d`](https://github.com/AresSC2/ares-sc2/commit/c11df7d833e54e2139eecd10674dfd3df4d70cc3))

## v2.0.1 (2024-02-09)

### Fix

* Only select persistent worker if enabled ([`47cabda`](https://github.com/AresSC2/ares-sc2/commit/47cabdaec7d1b0ec8a4177d45b30ce7ce915bacf))

## v2.0.0 (2024-02-08)

### Breaking

* migrate to cython-extensions-sc2 library / remove cython code ([`c7f3cb6`](https://github.com/AresSC2/ares-sc2/commit/c7f3cb661e21973e9494ba1180bca7f85d1c45a4))

### Documentation

* Update readme with contrib to docs guide ([`ff01848`](https://github.com/AresSC2/ares-sc2/commit/ff01848780fe5582f784db8dcc970ff23a354315))
* Update bots made with ares ([`d1736bd`](https://github.com/AresSC2/ares-sc2/commit/d1736bd693d0fce600dda47f2dedb8f113ac5c4f))
* Custom behavior tutorial ([`ec848d4`](https://github.com/AresSC2/ares-sc2/commit/ec848d44a5d57f95fed6db131a5f9d31b084c020))
* Unit squad initial tutorial file ([`2d7fb29`](https://github.com/AresSC2/ares-sc2/commit/2d7fb29859a235c96137e0a165bd51eb5796d4ce))
* Add group combat api ([`4fea72b`](https://github.com/AresSC2/ares-sc2/commit/4fea72bd98317ddc6f9ec19d5a823dacfacde17d))
* Add unit role tutorial ([`3f5291c`](https://github.com/AresSC2/ares-sc2/commit/3f5291ca00bc25d10db3043c8bbe8493b92dc802))

## v1.18.4 (2024-01-09)

### Fix

* Wrap squad merge in try except to check key error ([`666df90`](https://github.com/AresSC2/ares-sc2/commit/666df90d34c379b5cce4809e0a9621432f010fb0))

## v1.18.3 (2024-01-06)

### Fix

* Placement formation add gaps to help prevent unit block ([`0edf35b`](https://github.com/AresSC2/ares-sc2/commit/0edf35b8cedd329d11fc8fa98d37081804208aa3))

## v1.18.2 (2024-01-04)

### Fix

* Group behaviors return False if no units ([`c9aeebb`](https://github.com/AresSC2/ares-sc2/commit/c9aeebbbbd2e38bdbef19ca41e3c5594f59ab1d2))

## v1.18.1 (2024-01-04)

### Fix

* Circular import errors ([`3de527d`](https://github.com/AresSC2/ares-sc2/commit/3de527d480511a5c9642e37b8fd8f1a799f26910))

## v1.18.0 (2024-01-04)

### Feature

* Stutter group forward behavior ([`5171003`](https://github.com/AresSC2/ares-sc2/commit/5171003b3e79df1736d0fdc647be4a22c9c54f4f))
* Stutter group back behavior ([`9dc8e45`](https://github.com/AresSC2/ares-sc2/commit/9dc8e45e07bf1111a51dccb0d0c04a5758603ad2))
* Path group to target behavior ([`f425a72`](https://github.com/AresSC2/ares-sc2/commit/f425a72e3668bf710cfc690c8ba5115d7a57ce79))
* Keep group safe behavior ([`e4c2488`](https://github.com/AresSC2/ares-sc2/commit/e4c248890eda966f092a77b326117ff64a8f1788))
* Implement initial a-move group behavior ([`ce1eb39`](https://github.com/AresSC2/ares-sc2/commit/ce1eb3910032e49ba93a855c0d5830d1dfb52c31))
* Implement unit squad manager ([`f20b47c`](https://github.com/AresSC2/ares-sc2/commit/f20b47c7a4eb638a8791f2af84ac878c941da386))

## v1.17.1 (2023-12-15)

### Fix

* Don't try to select persistent worker if not enabled ([`4383924`](https://github.com/AresSC2/ares-sc2/commit/43839245dade28c4a53e76ed5785dcfb1b953084))

## v1.17.0 (2023-12-09)

### Feature

* Add production controller ([`123e1b8`](https://github.com/AresSC2/ares-sc2/commit/123e1b84b5b8181bfcaab5bb7f0993e321694333))
* Implement production controller ([`477947a`](https://github.com/AresSC2/ares-sc2/commit/477947a19dc26f4f4e0c2048fe5e3a4a42e9f62e))
* Add public method to complete build order ([`eceb294`](https://github.com/AresSC2/ares-sc2/commit/eceb2949bf9a9169637f4b89b0406fcd6c8fe82d))
* Add convienient pending methods ([`eac3ff1`](https://github.com/AresSC2/ares-sc2/commit/eac3ff1c9eea988526a3b59a0849e4a1588947d6))

### Fix

* Prevent mining crash if no townhalls ([`4d3f4c5`](https://github.com/AresSC2/ares-sc2/commit/4d3f4c57e6c8e15eed20ca22330e3f578256b02c))

### Documentation

* Add tutorial for production, add to readme ([`84b2d04`](https://github.com/AresSC2/ares-sc2/commit/84b2d040a178e342ee5858c7998f7ab0cabb4220))

## v1.16.0 (2023-12-03)

### Feature

* Build runner look ahead ([`b807e1b`](https://github.com/AresSC2/ares-sc2/commit/b807e1b220dcc1ef0e4028bde299abe7f5798188))
* Check existing structures on geyser ([`464eeb3`](https://github.com/AresSC2/ares-sc2/commit/464eeb36a154f1e3ef56c0c58745fa6ebbc95f91))

## v1.15.1 (2023-11-28)

### Fix

* Remove lru cache for proxies ([`27faf8d`](https://github.com/AresSC2/ares-sc2/commit/27faf8de6db5aec382a702d55f0237f2ec265cc2))
* Disable vespene boosting till it can be fixed ([`79a5e8f`](https://github.com/AresSC2/ares-sc2/commit/79a5e8fc5c19200891852faa93cce960a40ce424))

## v1.15.0 (2023-11-23)

### Feature

* Early game miners prefer minerals close to spawn ([`5d4c5b3`](https://github.com/AresSC2/ares-sc2/commit/5d4c5b3b54a1778ddb6e73f3c1a4aebf1f2c9880))
* Build structure behavior accepts closest to arg ([`ab7cee9`](https://github.com/AresSC2/ares-sc2/commit/ab7cee9904da4ea0a9dc831b956a48b7e948b9f3))

### Fix

* Coorent building size for bunker ([`9d8def0`](https://github.com/AresSC2/ares-sc2/commit/9d8def07050a5ddfef07235ba16dff857db3817a))

### Performance

* Mining behavior use existing unit tag dict ([`c003058`](https://github.com/AresSC2/ares-sc2/commit/c003058ba23d98f84ce8d6fb66227e80e9bd6246))

## v1.14.0 (2023-11-21)

### Feature

* Select worker with min health perc argument ([`d747986`](https://github.com/AresSC2/ares-sc2/commit/d74798639a0e57a68be8ea98de8d8d603e7195d7))
* Request placement closest to desired position ([`80a16d5`](https://github.com/AresSC2/ares-sc2/commit/80a16d59ddb17ac15ff071b1061df8946533293d))
* Persistent worker bool toggle when declaring builds ([`730a287`](https://github.com/AresSC2/ares-sc2/commit/730a287f46ab71f53911009a4eb89ae19714f43c))
* Improve worker safety behavior ([`fc77ddb`](https://github.com/AresSC2/ares-sc2/commit/fc77ddb1279965ec933165c7a12ea3d119155668))
* Add reaper grenade to grids ([`da222ab`](https://github.com/AresSC2/ares-sc2/commit/da222ab709f1536eee6ef5120d139976997a8c48))

### Fix

* Workaround to bug where resource bookkeeping is incorrect ([`1cc50aa`](https://github.com/AresSC2/ares-sc2/commit/1cc50aa321182105be65eee15c7bfb5f632f6f9d))

### Documentation

* Update README.md ([`fdd7c61`](https://github.com/AresSC2/ares-sc2/commit/fdd7c6194ecdf86035c780a277860f43fe3a8d14))

## v1.13.0 (2023-11-13)

### Feature

* Add behavior recipes ([`28178d8`](https://github.com/AresSC2/ares-sc2/commit/28178d847dd4a0d5efdd0ca71d35d0896cad5ea5))
* Add place predictive aoe behavior ([`f6008ac`](https://github.com/AresSC2/ares-sc2/commit/f6008ac743c787531eb435447f261978453b4af4))

### Documentation

* Fix internal links ([`c237d9e`](https://github.com/AresSC2/ares-sc2/commit/c237d9e413887e81ebf53633ed19bfe20dca2bcb))

## v1.12.1 (2023-11-04)

### Fix

* Return from find placement if nothing is available ([`c327345`](https://github.com/AresSC2/ares-sc2/commit/c327345d6b9c543f4c59e140f4ba1601a08be008))

## v1.12.0 (2023-11-03)

### Feature

* More extensive find alternative building placement ([`55f7062`](https://github.com/AresSC2/ares-sc2/commit/55f7062c8402010b3b1feb03f9815cb0a2277a11))

### Fix

* Ensure requested placements are removed properly ([`17bfef1`](https://github.com/AresSC2/ares-sc2/commit/17bfef12a7edd1f23cd80171427f16a58c60d8e3))

## v1.11.0 (2023-11-01)

### Feature

* Extra unit roles ([`a5717d1`](https://github.com/AresSC2/ares-sc2/commit/a5717d183bb641efc292fbc50de34599e2200177))

## v1.10.1 (2023-10-31)

### Fix

* Prevent removing dead scv from building tracker ([`5da3459`](https://github.com/AresSC2/ares-sc2/commit/5da3459a2a89de9236f3588ede557d3e21859bb8))
* Correct addon type id ([`bb89bf2`](https://github.com/AresSC2/ares-sc2/commit/bb89bf2c702cf9767354c9bb3b6adee0c21972e6))

## v1.10.0 (2023-10-29)

### Feature

* AddonSwap behavior ([`878219a`](https://github.com/AresSC2/ares-sc2/commit/878219a468ecf8e82b7d4652da2ff610abbacda1))
* Flying structure manager ([`013f040`](https://github.com/AresSC2/ares-sc2/commit/013f040e08e9635674660ddb30f993e96a6e38f9))
* Find placement at wall finds close alternative ([`6566e3f`](https://github.com/AresSC2/ares-sc2/commit/6566e3f545f3c09cafbb76f0e06a7049c0e840d5))

## v1.9.0 (2023-10-17)

### Feature

* Combat sim sets of EngagementResult ([`1008422`](https://github.com/AresSC2/ares-sc2/commit/100842299f2d97530ae56f2ab6f91af3b9c64b22))

## v1.8.0 (2023-10-12)

### Feature

* Add method to interact with combat sim ([`237ba44`](https://github.com/AresSC2/ares-sc2/commit/237ba44bf2c0aa406fcbb078e6e9241dc53fa4e8))

## v1.7.3 (2023-10-09)

### Fix

* Correct int type for weapon cooldown ([`a7cfd28`](https://github.com/AresSC2/ares-sc2/commit/a7cfd28b5709bf341caf01878418154d08543be0))

## v1.7.2 (2023-10-07)

### Fix

* Prevent stuck build runner ([`51c01bb`](https://github.com/AresSC2/ares-sc2/commit/51c01bb0c4b502c234201a6a235dd463f6ab3c63))

## v1.7.1 (2023-10-06)

### Fix

* Add src to sys path in load pickle file ([`425eafd`](https://github.com/AresSC2/ares-sc2/commit/425eafdeb0a5bf597a0af5d005aa25451218a6fe))
* Import for Ares when building from pickle ([`b2ea79b`](https://github.com/AresSC2/ares-sc2/commit/b2ea79b299f0345b5e750af74a3c4ae02c9b7a38))

## v1.7.0 (2023-09-10)

### Feature

* Reduce repetitive actions in mining and building ([`0cb9085`](https://github.com/AresSC2/ares-sc2/commit/0cb9085a57edd7f116e88d7f4799c888d219d758))

## v1.6.0 (2023-09-10)

### Feature

* Improve standard mining ([`9db655c`](https://github.com/AresSC2/ares-sc2/commit/9db655c2df274b77ba7ba0f3f52a77d29efce75a))

## v1.5.1 (2023-09-10)

### Fix

* Behaviors execute on correct frame ([`636c57b`](https://github.com/AresSC2/ares-sc2/commit/636c57b67dd0cce8a7dc392aadb53daacc7f4e18))

## v1.5.0 (2023-08-21)

### Feature

* Built AreBot object from pickled files ([`d09f0fd`](https://github.com/AresSC2/ares-sc2/commit/d09f0fdffa85d546cae341c9ed670d584e5514ed))

## v1.4.0 (2023-08-18)

### Feature

* Improve arcade map detection ([`c774f7a`](https://github.com/AresSC2/ares-sc2/commit/c774f7a963d7da9bfa38ccc74fad612aabf70fc8))

## v1.3.0 (2023-08-16)

### Feature

* Support arcade style maps ([`2d5e6b2`](https://github.com/AresSC2/ares-sc2/commit/2d5e6b2c4faa7148802d07b717441ab475484cb4))

### Documentation

* Major overhaul of all the documentation ([`eba0281`](https://github.com/AresSC2/ares-sc2/commit/eba0281b26ef786382a86aee1a5ecc8a7b76f208))

## v1.2.3 (2023-08-03)

### Fix

* Check enemy unit is in dict before removing ([`2016484`](https://github.com/AresSC2/ares-sc2/commit/201648412637dd5fee39b24127d50c48bbf85d90))

## v1.2.2 (2023-08-03)

### Fix

* Only add to building tracker if worker tag is not present ([`3a2046d`](https://github.com/AresSC2/ares-sc2/commit/3a2046d046e22447181d5342e2d87d23c6ddfef0))
* Safer auto supply ([`d762f4a`](https://github.com/AresSC2/ares-sc2/commit/d762f4a045a16550483f98a12a7c818d8d74b7e6))

## v1.2.1 (2023-08-03)

### Fix

* Accurate tracking of building counter ([`39a1a29`](https://github.com/AresSC2/ares-sc2/commit/39a1a2953f3beb700686003ee99714a3184b2359))
* Pass correct argument to `can_place_structure` ([`6ee0b93`](https://github.com/AresSC2/ares-sc2/commit/6ee0b9388292121bccf793ec4713c6ec9c85f32c))

## v1.2.0 (2023-08-02)

### Feature

* Own army value works correctly for all races ([`70e7d3b`](https://github.com/AresSC2/ares-sc2/commit/70e7d3bded41ec43cbe52d9b89f5488864d1ba4f))

## v1.1.0 (2023-07-31)

### Feature

* Timeout building worker if taking too long ([`98c9d72`](https://github.com/AresSC2/ares-sc2/commit/98c9d726d838105e2ad7d0a21817ffee1b1b5a34))
* Auto supply behavior ([`ccd053c`](https://github.com/AresSC2/ares-sc2/commit/ccd053c662fe3380173ef678993c044e7999bdab))
* Build structure behavior ([`b7d3b02`](https://github.com/AresSC2/ares-sc2/commit/b7d3b022c22aeab633bb6284780a7de0a898dc57))

## v1.0.0 (2023-07-29)

### Feature

* Protoss structure formation ([`2d7bb94`](https://github.com/AresSC2/ares-sc2/commit/2d7bb9432c47577b55e86daba9c4ad8c0a4da875))
* Cython pylon matrix covers function ([`d0b11a5`](https://github.com/AresSC2/ares-sc2/commit/d0b11a58f32c754a3c26e80a7e088ae8f625d5c8))

### Fix

* Check for ready townhalls before indexing ([`7a2444a`](https://github.com/AresSC2/ares-sc2/commit/7a2444ab08026962deda14ac04fd086de9c53fe5))

### Breaking

* `request_building_placement` and `can_place` accept structure_type argument rather then building_size ([`2d7bb94`](https://github.com/AresSC2/ares-sc2/commit/2d7bb9432c47577b55e86daba9c4ad8c0a4da875))

## v0.25.0 (2023-07-17)
### Feature

* All own units slim ([`274bba7`](https://github.com/AresSC2/ares-sc2/commit/274bba71c95db3d9eb6ef15cbc72b73d3fdde76e))

## v0.24.0 (2023-07-15)
### Feature

* Mining optimization ([`c5a7d72`](https://github.com/AresSC2/ares-sc2/commit/c5a7d72091b3de352956a98335058c165fef65f8))

## v0.23.1 (2023-07-11)
### Performance

* Replace dict.get() calls in mining ([`a295a35`](https://github.com/AresSC2/ares-sc2/commit/a295a35bca227b4a9d09010aea9f250c5cd1c076))

## v0.23.0 (2023-07-08)
### Feature

* Add worker kiting behavior ([`318eeab`](https://github.com/AresSC2/ares-sc2/commit/318eeabee6c7897ea55e17ce4d2104d19973bc38))

## v0.22.2 (2023-07-07)
### Fix

* Prevent find placement spam when there are no pylons ([`ea8dfe1`](https://github.com/AresSC2/ares-sc2/commit/ea8dfe18bf89e5c4dc6729fb83e6177cb0e73fa8))

## v0.22.1 (2023-06-30)
### Fix

* Ensure Point2 is passed to cy_sorted_by_distance_to ([`6b4ff8c`](https://github.com/AresSC2/ares-sc2/commit/6b4ff8cfd412d06831bfb29fc205c6949683bbde))

## v0.22.0 (2023-06-29)
### Feature

* Point2 towards cython function ([`91d41f1`](https://github.com/AresSC2/ares-sc2/commit/91d41f1024aa1d52a0929061b7028084f0cb012d))
* Unit is facing cython function ([`11759c1`](https://github.com/AresSC2/ares-sc2/commit/11759c1c6d5bde94b6da750241835ffd41968096))
* Sorted by distance to cython function ([`f511a9e`](https://github.com/AresSC2/ares-sc2/commit/f511a9e6b4ff780fab74f82bb878ae7d6860ae3e))

### Fix

* Increase influence range for melee units ([`e675c3c`](https://github.com/AresSC2/ares-sc2/commit/e675c3c72c4bd456932b62835fc6e919e863c72a))
* Remove from builder tracker if no target ([`134184e`](https://github.com/AresSC2/ares-sc2/commit/134184e4852bf4e0acd84734cdbb2cb7db46117f))

## v0.21.0 (2023-06-26)
### Feature

* Add stutter unit forward behavior ([`2477818`](https://github.com/AresSC2/ares-sc2/commit/247781882492ed9644a68355991ee530b6a145f2))
* Building manager handles blocked buildings ([`de9b793`](https://github.com/AresSC2/ares-sc2/commit/de9b793e14587ba6f70de4b2614be962518978e7))
* Improve debug drawings of building formation ([`5c43385`](https://github.com/AresSC2/ares-sc2/commit/5c43385668f56c2411ede0f3151eb50a9940712b))
* Reduce influence range of melee units ([`5a0655f`](https://github.com/AresSC2/ares-sc2/commit/5a0655f53eddbe1c8551b129cc09c5433a4dfc39))

### Fix

* Remove call to an attribute that doesn't exist ([`a4504d1`](https://github.com/AresSC2/ares-sc2/commit/a4504d11c652f2731cc61082b27ae2832246ba49))
* Check geyser exists before building ([`ef17730`](https://github.com/AresSC2/ares-sc2/commit/ef1773074652a426896ccc6a6f06b40c92849ae3))

### Documentation

* Add missing behaviors ([`3a44264`](https://github.com/AresSC2/ares-sc2/commit/3a4426468d6b25a628f8963bedccdc810fb847da))

## v0.20.0 (2023-06-22)
### Feature

* Mining workers have basic self defence ([`27ec3a5`](https://github.com/AresSC2/ares-sc2/commit/27ec3a5b2a836193fa8745d786a746334fe7c000))

### Fix

* Scv can actually resume building unfinished structure ([`8ecf85b`](https://github.com/AresSC2/ares-sc2/commit/8ecf85b51d1797b04c047183a8fb9db8dca600ce))
* Grids are reset after step is complete, not during ([`e3f635d`](https://github.com/AresSC2/ares-sc2/commit/e3f635d860fcc5fe0cb055474f668fb28a03f2bb))

## v0.19.0 (2023-06-21)
### Feature

* Add enemy to base manager ([`b06b52c`](https://github.com/AresSC2/ares-sc2/commit/b06b52c29e6ea629c173c5a26e0250b871275aeb))

## v0.18.0 (2023-06-19)
### Feature

* Handle missing workers in building tracker ([`3dabbc8`](https://github.com/AresSC2/ares-sc2/commit/3dabbc8f55f38b47d3a4466e13f48327aa656f46))

### Fix

* Pick enemy target returns the correct value ([`6965a6d`](https://github.com/AresSC2/ares-sc2/commit/6965a6d809b986d937b17f7f69e785daf4c8934a))
* Reorder spawn logic so unit is built if only one possible spawn option ([`14431e7`](https://github.com/AresSC2/ares-sc2/commit/14431e7432f30c6ec66cdcf4b54bfe73e6945df6))

### Performance

* Make use of cython functions in mining ([`6d39fb8`](https://github.com/AresSC2/ares-sc2/commit/6d39fb813e6ceeaef8ce1eaaf5b462e821a7c6f4))

## v0.17.0 (2023-06-17)
### Feature

* Implement new unit behaviors ([`d51aec1`](https://github.com/AresSC2/ares-sc2/commit/d51aec1f97746ea4953b98454b575bcad8abd7c0))
* Attack_ready / pick_enemy_target cython functions ([`e00a9b7`](https://github.com/AresSC2/ares-sc2/commit/e00a9b721a9b2f60192b554e86e44f40ee2c928f))
* Cython in_attack_range function ([`9490bfe`](https://github.com/AresSC2/ares-sc2/commit/9490bfe8a6f9775203984afa8bbd851a153d1457))
* Update cython notebook ([`6c4b5c7`](https://github.com/AresSC2/ares-sc2/commit/6c4b5c7cd7b0c8cfe1366ee4de14dc9f05d16c20))
* Include additional unit data ([`f549462`](https://github.com/AresSC2/ares-sc2/commit/f54946222e348cc6c87d25ac9880bcca05c43f1b))

### Fix

* Influence updated correctly ([`b0f15ec`](https://github.com/AresSC2/ares-sc2/commit/b0f15ec31bb6406cddab9de57e78582ff5538bb2))

## v0.16.1 (2023-06-13)
### Fix

* Change to new constant_worker_production_till ([`c37ed11`](https://github.com/AresSC2/ares-sc2/commit/c37ed11d71b2fb2d879e376131d022dd2d691fb1))

## v0.16.0 (2023-06-13)
### Feature

* Cython unit pending function ([`f0bacb5`](https://github.com/AresSC2/ares-sc2/commit/f0bacb543bc3aa84f99afa2b2dffdd6bf33d22db))

### Fix

* Only attempt orbital upgrade from command center ([`8b67862`](https://github.com/AresSC2/ares-sc2/commit/8b67862727620c50df46ea06b0874895bc1035d3))
* Spawn controller accounts for alias units ([`22989b4`](https://github.com/AresSC2/ares-sc2/commit/22989b42af223166c61fac6222f25e8376affb33))

## v0.15.0 (2023-06-13)
### Feature

* Add unit pending to cython notebook ([`0580017`](https://github.com/AresSC2/ares-sc2/commit/0580017870f28392b8d1c806b1440599d76795b5))

## v0.14.0 (2023-06-07)
### Feature

* Add climber grid with mediator request ([`c9b58e6`](https://github.com/AresSC2/ares-sc2/commit/c9b58e604b3cac61db6eef24f4f541fdbb7c2a72))

## v0.13.0 (2023-06-03)
### Feature

* Support tracking of widow mine attack cooldown ([`07e8f19`](https://github.com/AresSC2/ares-sc2/commit/07e8f198f723231d15e9c2025eefc3e4ea3fdaac))
* Cythonize a few more functions / update notebook ([`8e00b8a`](https://github.com/AresSC2/ares-sc2/commit/8e00b8aeac6e2c46c2311d11f1ba045df9ee5f65))

## v0.12.0 (2023-05-25)
### Feature
* Combat behavior system ([`838a3c2`](https://github.com/AresSC2/ares-sc2/commit/838a3c23d53d6a7a526335b9091f83132fffc7cf))
* Add unload container methods ([`e6e2cec`](https://github.com/AresSC2/ares-sc2/commit/e6e2cecd9be98324f9774ac5971f4d32eafb0aba))
* Add chosen opening property to build runner ([`f1743b1`](https://github.com/AresSC2/ares-sc2/commit/f1743b10711628007e818564ccf591e74248a8a9))
* Python to cython notebook ([`0ff759d`](https://github.com/AresSC2/ares-sc2/commit/0ff759dc005badb93bdd8ff9a04bf4127439c04d))
* Cython is_position_safe and closest_to functions ([`8289031`](https://github.com/AresSC2/ares-sc2/commit/8289031fe18a1c02ef7a7e168841bb72ce9fa1f2))

### Documentation
* Add combat behavior documentation ([`7c612c4`](https://github.com/AresSC2/ares-sc2/commit/7c612c4cc8069d68c92a6f25d7e36c703d8ee69a))

## v0.11.1 (2023-05-17)
### Fix
* Add missing techlab type set ([`bd0e004`](https://github.com/AresSC2/ares-sc2/commit/bd0e00451439c3cc7494d5aee656776454538e68))

## v0.11.0 (2023-05-17)
### Feature
* Implement spawn controller ([`1d92b95`](https://github.com/AresSC2/ares-sc2/commit/1d92b950d9a605e375e9df18d58002e13f7c1dea))
* Save techlab and reactor tags ([`7cba27f`](https://github.com/AresSC2/ares-sc2/commit/7cba27f90221bfd2ccb853ec81d617dc85693a94))
* Implement unit tech ready method ([`5fe8cf2`](https://github.com/AresSC2/ares-sc2/commit/5fe8cf2746bb86f6aedfcbc9a412c11f4aa35444))
* Add own unit count method ([`1fd4830`](https://github.com/AresSC2/ares-sc2/commit/1fd48306fe107d9a9e295022297b3c899c0288bc))

### Fix
* Unreachable logic ([`5c78d77`](https://github.com/AresSC2/ares-sc2/commit/5c78d773ee2bb1aa2bcf2f7e59d8e3ecfcc931f5))
* Prevent crash if unit type not present in unit cache dict ([`b205a46`](https://github.com/AresSC2/ares-sc2/commit/b205a46d9920ada56f8783cb8bcd62859ae7ec39))

### Documentation
* Add spawn controller to mkdocstrings ([`042fd7e`](https://github.com/AresSC2/ares-sc2/commit/042fd7eb628a5ccd368e63273b39508d81e53e28))

## v0.10.0 (2023-05-09)
### Feature
* Allow extending managers ([`ff96d4e`](https://github.com/AresSC2/ares-sc2/commit/ff96d4e59464c6f29547d9759a843c6d737f03df))
* Add support for custom managers ([`aee5a38`](https://github.com/AresSC2/ares-sc2/commit/aee5a382966b576d14099840efb95ba466c0caf2))

### Documentation
* Provide example of a custom manager ([`4476283`](https://github.com/AresSC2/ares-sc2/commit/44762839b16de8a0479979f38d2af48035739206))

## v0.9.0 (2023-05-09)
### Feature
* Basic test of whether AresBot can start ([`06245af`](https://github.com/AresSC2/ares-sc2/commit/06245afd24b0b3084c1e04973c215a4efb7e5e91))

## v0.8.0 (2023-05-09)
### Feature
* Build step contains supply count and constant workers ([`12f4bb0`](https://github.com/AresSC2/ares-sc2/commit/12f4bb099cabdee9d54012746788caf2e8ed27be))

## v0.7.0 (2023-05-08)
### Feature
* Add terran building location notebook ([`a5d080d`](https://github.com/AresSC2/ares-sc2/commit/a5d080d37b244166cfa1d7cecc935a373294f3ce))
* Implement new placement manager ([`76e2c28`](https://github.com/AresSC2/ares-sc2/commit/76e2c2853f88d0d70f517cdd281913a800c14a67))
* Implement placement solver in cython ([`9fba4a2`](https://github.com/AresSC2/ares-sc2/commit/9fba4a2228a023c10ef17a33b51d44dddeb9a18e))

## v0.6.0 (2023-05-07)
### Feature
* Add orbital option to build runner ([`b74a9b2`](https://github.com/AresSC2/ares-sc2/commit/b74a9b23a707570a5364f787c0d1b3a43610d5cf))
* Persistent building worker ([`57016ec`](https://github.com/AresSC2/ares-sc2/commit/57016ec0e944b392b154edd54786c2c046f18088))

## v0.5.0 (2023-04-20)
### Feature
* Port flood fill algorithm to cython ([`3e318c3`](https://github.com/AresSC2/ares-sc2/commit/3e318c3cb75a04f5995d9866ce6a1fc169de1908))

## v0.4.1 (2023-04-11)
### Fix
* Check all units for unit trained from ([`3ca162a`](https://github.com/AresSC2/ares-sc2/commit/3ca162ad16badf340c0485b1d5a0b6b90065f429))
* Import errors ([`0698c07`](https://github.com/AresSC2/ares-sc2/commit/0698c074fb95269179f4947507b7827594b54843))

## v0.4.0 (2023-04-08)
### Feature
* Generic chrono option in build runner ([`70e4f37`](https://github.com/AresSC2/ares-sc2/commit/70e4f3724f24ca06bf30153672f382bceadf4ecc))
* Implement new build order runner ([`53d77c7`](https://github.com/AresSC2/ares-sc2/commit/53d77c70f7c25f14889e7b256e640f55a7f28832))

### Fix
* Bot runs without a builds.yml file ([`2892bc4`](https://github.com/AresSC2/ares-sc2/commit/2892bc4c6c371a086920ac9d5b2acc3a10abc3ff))
* Cycling through builds works ([`b8ded14`](https://github.com/AresSC2/ares-sc2/commit/b8ded141a4d8ec6d4c7f112533055e33f18ab6e3))

### Documentation
* Document build runner / mediator / behaviors ([`0e7079a`](https://github.com/AresSC2/ares-sc2/commit/0e7079a49415722a59ce7359059f78c2af4f1475))
* Add docstrings to data manager ([`09de2cc`](https://github.com/AresSC2/ares-sc2/commit/09de2ccf6a449fbb28ee3a460da81ebee3a1eb20))

## v0.3.0 (2023-03-17)
### Feature
* Implement custom user config file ([`10c77e9`](https://github.com/AresSC2/ares-sc2/commit/10c77e906301cf31dae4fb52c160b0e94c391f83))

## v0.2.0 (2023-03-02)
### Feature
* Extract mining logic to behavior class ([`31eb6f8`](https://github.com/AresSC2/ares-sc2/commit/31eb6f89322c2f28ef4e76f3692572fd29fdc425))
* Behavior interface ([`b7a5d83`](https://github.com/AresSC2/ares-sc2/commit/b7a5d83e50228409615ac101acc380e79754068e))

## v0.1.0 (2023-02-22)
### Feature
* Add BaseProduction ([`494258e`](https://github.com/AresSC2/ares-sc2/commit/494258e55fb3852a4d01a922b7545e6a6f05fe5c))
* Add ManagerMediator ([`cfb34dc`](https://github.com/AresSC2/ares-sc2/commit/cfb34dc9f4d4bbcca2ea4aeed9707d6b97637cb5))
* Add CombatManager ([`13ebc22`](https://github.com/AresSC2/ares-sc2/commit/13ebc220cba6fff6a74994eed5fd4d3b04525017))
* Add the remaining managers ([`ad5ef08`](https://github.com/AresSC2/ares-sc2/commit/ad5ef085d98ed4e719cebc1f3e87bba5aa9cdb2f))
* Add sc2_helper ([`369005d`](https://github.com/AresSC2/ares-sc2/commit/369005d1349a0ee49a471779f1374d78de2585d0))
* Add unit tracking managers ([`ad3d918`](https://github.com/AresSC2/ares-sc2/commit/ad3d9186e5188ecdbad62d452633af5a45ae420d))
* Add production and resource managers ([`beb7725`](https://github.com/AresSC2/ares-sc2/commit/beb7725aa7a21bcadbed1e53cc9d65c4787b83d0))
* Add a couple extra managers ([`3443e29`](https://github.com/AresSC2/ares-sc2/commit/3443e29588897248843e36ad6859b2a4fa3aac08))
* Add dicts directory ([`54767c0`](https://github.com/AresSC2/ares-sc2/commit/54767c0d7b576febace99352b1f444b822ca9261))
* Begin adding bot skeleton ([`8dcdbee`](https://github.com/AresSC2/ares-sc2/commit/8dcdbeedb5ff59354651499eab115317f9b1e6ef))
* Add sc2 and mapanalyzer ([`13f3bda`](https://github.com/AresSC2/ares-sc2/commit/13f3bda3b7922e00d2e620fa02e0449230ea0015))

### Fix
* Add main import to init ([`200bda7`](https://github.com/AresSC2/ares-sc2/commit/200bda70f1277388926f889e71a5308c7d86dae9))

### Documentation
* Add link to documentation in readme ([`cb6a5cf`](https://github.com/AresSC2/ares-sc2/commit/cb6a5cff330a74c6e885fc984f44bba3e0f369c1))

## v0.0.2 (2023-01-25)
### Fix
* Poetry installs on docker ([`d5e7054`](https://github.com/AresSC2/ares-sc2/commit/d5e70543fc313599da4e31310596681131cc54d3))

## v0.0.1 (2023-01-25)

