# Result JSON schema

We use dataclasses to define shape of data used to
communicate between application core and jinja.

## Schema definition

- **result**
  _boolean_

  > Flag summarizing overall compliance. It should be set to `true` when and only when all checks in all sections are passing. Otherwise, it should be set to `false`.

- **major_problems**
  _list_

  > List of failed important checks - it should contain strings that briefly describe what kind of major issues were found on a cluster.

- **sections**
  _list_

  > List of checks' sections.

  - **name**
    _string_

    > Section's name. It should be brief, yet descriptive enough title encompassing all checks from a particular category. Allowed characters are ASCII letters and digits.

  - **description**
    _string_

    > More detailed information about a particular group of checks.

  - **major_problems**
    _list_

    > Important issues causing checks from this section to fail.

  - **result**
    _boolean_

    > Flag representing particular section's result. Section is considered failed if any of the checks inside failed - in this case, this value should be set to `false`. Otherwise - it must be `true`.

  - **checks**
    _list_

    > List of all checks for particular section.

    - **name**
      _string_

      > Checks's name. It should succinctly and unambiguously name a particular check.

    - **description**
      _string_

      > More detailed information about a particular check. It should delineate check's mode of action, what it's possible values mean and what result is acceptable.

    - **check**
      _dictionary_

      > Check's result and values, both measured and expected.

      - **result**
        _boolean_

        > Result of check's operation. It should be set to `true` when and only when check is passing. Otherwise, it must be `false`.

      - **measured**
        _string_

        > Value reported by check directly representing parameter being measured. It should return only values covered in `description` section of specified check.

      - **expected**
        _string_

        > Proper value representing acceptable condition for check to pass. It should not only describe the value itself, but also, when applicable, point out what is considered acceptable, e.g., by using majority sign in front of said value.

      - **major_issue**
        _string_

        > Critical issue, which caused this check to fail.

### Example result JSON

```json
{
  "result": false,
  "major_problems": ["Critical error!"],
  "sections": [
    {
      "name": "Foo",
      "result": true,
      "major_problems": [],
      "checks": [
        {
          "name": "sys.max_opened_foobars",
          "description": "Lorem ipsum dolor sit amet",
          "check": {
            "result": true,
            "measured": "1337",
            "expected": "> 1000"
          }
        },
        {
          "name": "sys.min_foobar_value",
          "description": "Consectetur adipiscing elit",
          "check": {
            "result": true,
            "measured": "13370",
            "expected": "< 20000"
          }
        }
      ]
    },
    {
      "name": "Bar",
      "result": false,
      "major_problems": ["Critical error!"],
      "checks": [
        {
          "name": "Foobar version",
          "description": "Sed do eiusmod tempor incididunt ut labore",
          "check": {
            "result": false,
            "measured": "1337",
            "expected": "> 9000"
            "major_problem": "Critical error!",
          }
        },
        {
          "name": "Foobar admin privileges",
          "description": "Ut enim ad minim veniam",
          "check": {
            "result": true,
            "measured": "true",
            "expected": "true"
          }
        }
      ]
    }
  ]
}
```
