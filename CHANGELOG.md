# Changelog

<!--next-version-placeholder-->

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

