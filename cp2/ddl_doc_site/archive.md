# The *archive* section
The *archive* section defines the data (files, parameters, running time, …) to be stored for each experiment performed with original data uploaded by the user. The normal behaviour is to archive only the original data uploaded by the users. However, a demo editor can also allow to store all the experiments done even if the data does not come from an upload (see the *archive_always* field).

| key | **description** | **req** |
|:---|:---|:--:|
| files | (key, value) pairs where key is the file to archive and value is the name. | no |
| hidden_files | This field contains files as in the above one. This is used to store files required for a correct reconstruction of an experiment but that the demo editor does not want to show in the archive. | no |
| params | List of parameters to archive. | no |
| enable_reconstruct | Show a button to reconstruct an experiment stored in the archive. | no |
| archive_always | The archive will store the experiments even if they are performed with the data proposed by the demo (if the private mode is not set). | no |

The *archive* section, properties

#### Example:

Here, we see DDL’s needed to activate the reconstruct and archive_always options. They also specify the files and params that must be stored in a particular order. The running time for each execution is also stored.\

``` json
"archive":
  {
    "enable_reconstruct": true,
    "archive_always": true,
    "files" : 
      { "input_0.png"                 : "input image",
        "primitives.txt"              : "Primitives"
      },
    "params" :  
      [ "high_threshold_canny", 
        "initial_distortion_parameter", 
        "angle_point_orientation_max_difference" ],
    "info"   : { "run_time": "run time" }
  }
```
