# Changelog

<!--next-version-placeholder-->

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

