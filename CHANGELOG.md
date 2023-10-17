# Changelog

<!--next-version-placeholder-->

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

