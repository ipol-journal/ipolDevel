# The *general* section
The general section describes global information about the demo. It is a set of (key, value) pairs, described in the following table. The column *req* refers to a required field. This type of tables will be used in all the sections of this document.

| key | **description** | **req** |
|:---|:---|:--:|
| demo_title | Title of the demo. | no |
| description | Description to be shown at the beginning of the demo page. It contains HTML or plain text as a single string. | no |
| input_description | Description of the inputs. It contains HTML as a single string or as an array of string that will be concatenated and separated with spaces. | no |
| param_description | Description for the parameters. It contains HTML code as a single string or as an array of string that will be concatenated and separated with spaces. | no |
| xlink_article | Link to the article webpage | no |
| requirements | It specifies particular requirements needed for the execution of the demo, separated by commas. e.g. Matlab. | no |
| custom_js | It allows to give the URL of a custom Javascript file. This script contains extra JS code that allows to personalize the interaction and look of the front-end. It should only be used in very special cases there there is not any other alternative than overwriting the default behavior or look. | no |
| timeout | It specifies maximum time in seconds allows to execute the algorithm. If the execution takes longer than the specified time the system stops the execution. | no |

Fields in the *general* section.
