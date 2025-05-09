# CHANGELOG


## v0.2.0 (2025-05-08)

### Bug Fixes

- Rename profile_id to user_id in get_user_profile endpoint for consistency and clarity
  ([`8259596`](https://github.com/fotapol/fastboosty-profile_service/commit/8259596ffcfcf3a019ba2e93b810f5e0792e1aed))

- Update GHCR token reference in CD workflow
  ([`55312de`](https://github.com/fotapol/fastboosty-profile_service/commit/55312de3b8a610ba3ca409f01ec5c7375865de82))

- Update tests with new logic. Add new tests for new endpoint. Delete deprecated tests.
  ([`89af643`](https://github.com/fotapol/fastboosty-profile_service/commit/89af6432899fea6184f86c4aea64538d806a465f))

### Chores

- Styling code using ruff formater
  ([`a41e2c7`](https://github.com/fotapol/fastboosty-profile_service/commit/a41e2c754a85520eb7d205bf022fa6bfaedc80d6))

- Styling code using ruff formater
  ([`336ea96`](https://github.com/fotapol/fastboosty-profile_service/commit/336ea96d5758838f32edb859371e3c3ee582ccf3))

- Styling code using ruff formater
  ([`1c00332`](https://github.com/fotapol/fastboosty-profile_service/commit/1c0033260d5e4518ee0741cab68c2a06a9bd78f6))

### Features

- Add Continuous Delivery workflow for automated releases. Update name for ci.yaml
  ([`0d6b352`](https://github.com/fotapol/fastboosty-profile_service/commit/0d6b3526e6a8b3ca19b66b3ecf65a5b34f7211dd))

- Add profile retrieval endpoint by user ID
  ([`cfcaa84`](https://github.com/fotapol/fastboosty-profile_service/commit/cfcaa846ef267196fc60e917e9001178d05ac69d))

- Enhance profile retrieval and update logic with default profile creation
  ([`5cc8f8d`](https://github.com/fotapol/fastboosty-profile_service/commit/5cc8f8dee5cd9f52c6148a3912c729e05c545bf2))

- Implement caching for user profile retrieval and enhance error handling. Add AWS S3 support in
  get_user_profile endpoint
  ([`402620a`](https://github.com/fotapol/fastboosty-profile_service/commit/402620abeae522a41aedb054d47c184203766a5a))


## v0.1.0 (2025-05-06)

### Bug Fixes

- Add PostgreSQL service configuration to CI workflow
  ([`fa3805c`](https://github.com/fotapol/fastboosty-profile_service/commit/fa3805cf63e750086cfb4ae0034ef04a0ca61f0b))

- Add SQLALCHEMY_DATABASE_URI to environment variables for pytest
  ([`6a476dd`](https://github.com/fotapol/fastboosty-profile_service/commit/6a476ddf586e94345b1eb2812807ae00c20a3b9b))

- Add sync command in CI workflow
  ([`71856b1`](https://github.com/fotapol/fastboosty-profile_service/commit/71856b1959e033523c633da95f0fa67f033b1f47))

- Change url for configuring GITHUB_TOKEN
  ([`98d3696`](https://github.com/fotapol/fastboosty-profile_service/commit/98d3696f47b8ad694126836efc3b0fdf49284147))

- Correct environment variable names for pytest in CI workflow
  ([`1b555f9`](https://github.com/fotapol/fastboosty-profile_service/commit/1b555f9f96cf35223223051d561c8affbed3e09b))

- Fix critical bug with create_or_update_my_profile endpoint
  ([`f49b96e`](https://github.com/fotapol/fastboosty-profile_service/commit/f49b96e675cfdb4d81a5ce5d44356930a79e1cfa))

- Prevent updating profile fields with None values to allow partial updates
  ([`4de989d`](https://github.com/fotapol/fastboosty-profile_service/commit/4de989d700e47bb68cc5bb3079a005b9490bdfca))

- Remove AUTH_SERVICE_URL from config and .env.sample
  ([`ab3eee4`](https://github.com/fotapol/fastboosty-profile_service/commit/ab3eee4284c913481c9f08ff7255af65906eda20))

- Remove unused python-magic dependency from pyproject.toml and uv.lock
  ([`bce9c2c`](https://github.com/fotapol/fastboosty-profile_service/commit/bce9c2c24a2f19fbf2fd09fcc0a2b9217479a625))

- Set default JWT_SECRET_KEY in conftest.py for correct testing in the ci.yaml
  ([`b97f639`](https://github.com/fotapol/fastboosty-profile_service/commit/b97f6390325db82a5a494d00b2e760686ddb01ca))

- Update actions versions and improve Git configuration for private repo access
  ([`74f3d45`](https://github.com/fotapol/fastboosty-profile_service/commit/74f3d4579f20349c8b44980c1e662ae79de61ee6))

- Update import paths and set default values for ProfileUpdate fields
  ([`6b0509c`](https://github.com/fotapol/fastboosty-profile_service/commit/6b0509cf476e41066164e8bb9f6bcdd389ae02bd))

- Update PostgreSQL environment variables for CI workflow
  ([`78d4480`](https://github.com/fotapol/fastboosty-profile_service/commit/78d4480486981ad70aa4a3e71b4184e8f2a54bba))

- Update test database lifecycle management in conftest.py
  ([`b687510`](https://github.com/fotapol/fastboosty-profile_service/commit/b687510a989e4252d3dbf055386a6cb56b9585b7))

- **profile**: Update port configuration and adjust auth service URL in dependencies
  ([`94bd056`](https://github.com/fotapol/fastboosty-profile_service/commit/94bd05628d6a7e907adbcd512c7dff0d724b6946))

### Features

- Add asgi-lifespan dependency and update related configurations
  ([`55d1a46`](https://github.com/fotapol/fastboosty-profile_service/commit/55d1a4611dbf8a765de95848f423dc7a21a2e875))

- Add async libraries to work with AWS S3
  ([`0dbc53a`](https://github.com/fotapol/fastboosty-profile_service/commit/0dbc53a00cd07d517391ed0424a3adf82a5fdb08))

- Add auth-lib dependency for authentication handling
  ([`0634632`](https://github.com/fotapol/fastboosty-profile_service/commit/0634632819bd9324de30aecea997b8f207f6ca4d))

- Add AWS configuration to .env.sample and update S3Client initialization
  ([`d59d199`](https://github.com/fotapol/fastboosty-profile_service/commit/d59d1991930bfa4d20221734a21b199a00bae3f5))

- Add AWS credentials to CI configuration for testing
  ([`cc7bada`](https://github.com/fotapol/fastboosty-profile_service/commit/cc7bada10b5c21dbc6ad068bbae2b876e587a249))

- Add AWS S3 configuration to settings and initialize S3Client in the lifespan section
  ([`08030b8`](https://github.com/fotapol/fastboosty-profile_service/commit/08030b86653e4da91eaa39886e32154be45b385b))

- Add CI workflow for testing with Python and linter
  ([`d6cbf7b`](https://github.com/fotapol/fastboosty-profile_service/commit/d6cbf7b6b6ec552f1a08220afcacfb5a77d1f847))

- Add cleanup fixture to reset database state before each test
  ([`dd5f828`](https://github.com/fotapol/fastboosty-profile_service/commit/dd5f828121478c48c1e243756e4ffea9b8121e99))

- Add GITHUB_TOKEN configuration for auth_lib in CI workflow
  ([`95a601d`](https://github.com/fotapol/fastboosty-profile_service/commit/95a601db45cb673dd18a1241f36d17c4317c54d8))

- Add initial .dockerignore file to exclude Python cache
  ([`07ed657`](https://github.com/fotapol/fastboosty-profile_service/commit/07ed65705e1940fbe7bfaaa1c8518d0b3eae5a4b))

- Add mock Redis client to test application setup
  ([`2caf82f`](https://github.com/fotapol/fastboosty-profile_service/commit/2caf82f5778490921aba1f3babc32173c2fb4bc4))

- Add python-semantic-release package. Update main.py.
  ([`8368819`](https://github.com/fotapol/fastboosty-profile_service/commit/8368819889446498ded055ec4a528f02fbd9eed4))

- Add Redis configuration to CI for testing environment
  ([`2994f06`](https://github.com/fotapol/fastboosty-profile_service/commit/2994f0681a12384add44aeedb7faa8b358db6502))

- Add Redis configuration to environment and update dependencies
  ([`ecb4a9b`](https://github.com/fotapol/fastboosty-profile_service/commit/ecb4a9bdef8f6fcba97ff45cfbdc3c81d63460b0))

- Add s3_client initialization to test lifespan
  ([`c9c0150`](https://github.com/fotapol/fastboosty-profile_service/commit/c9c0150da4569618ae24c9d3ed8d8cc22b893477))

- Add S3Client class for asynchronous file uploads and URL generation
  ([`b33bec4`](https://github.com/fotapol/fastboosty-profile_service/commit/b33bec41f5d9eb3c70375b2560279b912d0d8d63))

- Add test fixtures and database setup for pytest-asyncio integration
  ([`bca7ab2`](https://github.com/fotapol/fastboosty-profile_service/commit/bca7ab20143f6a3b71dee52414698b597c045214))

- Add tests for profile creation and updates
  ([`b643516`](https://github.com/fotapol/fastboosty-profile_service/commit/b64351648b1af1bdff13be435d71dd93845f56d3))

- Add tests for profile retrieval in test_api.py
  ([`5f83119`](https://github.com/fotapol/fastboosty-profile_service/commit/5f831193e7d7cc6fabb6df1cf4b7198b93a0af3f))

- Added configuration for a test PostgreSQL database in the .env.sample file. Included 'pytest-cov'
  as a development dependency for coverage reporting.
  ([`66f3313`](https://github.com/fotapol/fastboosty-profile_service/commit/66f3313a3f13a308417e500a244633b52330263c))

- Enhance profile update to include avatar URL generation and improve error handling
  ([`b0af015`](https://github.com/fotapol/fastboosty-profile_service/commit/b0af015bddb29b79ef7d8a6e3441b66c0376acde))

- Implement upload_icon endpoint for S3 file uploads
  ([`7858b1f`](https://github.com/fotapol/fastboosty-profile_service/commit/7858b1f4da76a66574e9fa6fe37c5507704f6732))

- Improve test setup with async session management and application lifecycle handling
  ([`4fd2e56`](https://github.com/fotapol/fastboosty-profile_service/commit/4fd2e562ba0c31109f0a267b6c2b9d70518fd0ce))

- Improve type hints, error handling, remove extra comments.
  ([`507469f`](https://github.com/fotapol/fastboosty-profile_service/commit/507469f626b4ab992c79c9354c3c605044122b63))

- Integrate Redis caching for user profile retrieval and updates
  ([`dba3938`](https://github.com/fotapol/fastboosty-profile_service/commit/dba3938c350ff1163654595bc5414e2beddc2eeb))

- Move endpoint.py to router folder. Fix import path
  ([`0add0ab`](https://github.com/fotapol/fastboosty-profile_service/commit/0add0ab11a9a6ca00511b3a71441f418935e3fcc))

- Refactor profile handling to integrate S3 avatar URL generation and remove upload_icon module.
  Delete used file
  ([`1c75a80`](https://github.com/fotapol/fastboosty-profile_service/commit/1c75a80c8146dd146385ee4b44388cbf7cf5e09e))

- Remove deprecated import of CurrentUserUUID from dependencies and add new import from new package
  ([`1bf9e72`](https://github.com/fotapol/fastboosty-profile_service/commit/1bf9e7214da3691b08eba1eb420565d9130be819))

- Update old tests for using mocked s3_client. Add new tests with icon upload
  ([`6eb8b94`](https://github.com/fotapol/fastboosty-profile_service/commit/6eb8b942d4bd2e9bcf462ed38556063a6140e417))

- Update profile tests to use dependency injection for session management and improve user ID
  handling
  ([`f92f2b9`](https://github.com/fotapol/fastboosty-profile_service/commit/f92f2b91c42d86f678176220210d56377358492d))

- Update Python version to 3.13 in the Dockerfile for improved dependency installation. Update
  auth-lib version
  ([`d137390`](https://github.com/fotapol/fastboosty-profile_service/commit/d13739089b7579367462279e9c8dc20f5aa4e798))

- **profile**: Add DB connection, Profile model, and schemas
  ([`81b9140`](https://github.com/fotapol/fastboosty-profile_service/commit/81b9140e894e7f2f4412e25b9a5ec454562509a3))

- **profile**: Add entrypoint script for database readiness and migrations
  ([`bf4abc6`](https://github.com/fotapol/fastboosty-profile_service/commit/bf4abc63c127ad541e41cf9e4ce38063bc41703c))

- **profile**: Add initial profile model and update migration scripts
  ([`d9610d3`](https://github.com/fotapol/fastboosty-profile_service/commit/d9610d3b469b6d30e50a564110665a040e4659ee))

- **profile**: Add profile API router and setup main app
  ([`9f4d9a0`](https://github.com/fotapol/fastboosty-profile_service/commit/9f4d9a0906af9c47f781dc991037739de1c0e46c))

- **profile**: Implement auth dependency via auth_service call
  ([`2f86be4`](https://github.com/fotapol/fastboosty-profile_service/commit/2f86be44678b760b11d1e8c5b1e2bd1b1cd244dd))

- **profile**: Initial setup for profile service
  ([`7bd5eb7`](https://github.com/fotapol/fastboosty-profile_service/commit/7bd5eb704e3a1c44b9cd1824abb0adc9f37fca3b))

- **profile**: Refactor JWT token handling in dependencies and update authorization header
  ([`31e9c7d`](https://github.com/fotapol/fastboosty-profile_service/commit/31e9c7df272a85a42549a078248fa2941bab3cfd))

### Refactoring

- Clean up comments in database and redis client modules
  ([`f4dee4e`](https://github.com/fotapol/fastboosty-profile_service/commit/f4dee4eae1ec27f973b7b9f340ba8363366be62a))

- Clean up imports and remove unused per-file ignores in test configuration. Fix E501 in test_api.py
  ([`2dfd52b`](https://github.com/fotapol/fastboosty-profile_service/commit/2dfd52b837d68d465eeb8401589da5474a9544d9))

- Code styling one file with ruff formater
  ([`6a84846`](https://github.com/fotapol/fastboosty-profile_service/commit/6a84846ae6a50c2a0114d48a54ebe5cb0ede1311))

- Code styling using ruff formater
  ([`dbe4d1c`](https://github.com/fotapol/fastboosty-profile_service/commit/dbe4d1c40311609c526306c180721baee13ef403))

- Code styling with ruff formater
  ([`3f7cf3d`](https://github.com/fotapol/fastboosty-profile_service/commit/3f7cf3d4407226cb385ddffedbdcd1bbfd09a680))

- Make error more informative
  ([`96cc356`](https://github.com/fotapol/fastboosty-profile_service/commit/96cc356bc420eb757837ca78fbacc28f62ebe4b0))

- Move rollback calls in profile tests to fixtures and improve timestamp assertions
  ([`20b220e`](https://github.com/fotapol/fastboosty-profile_service/commit/20b220e5448324ed065f84b62257a42036209526))
