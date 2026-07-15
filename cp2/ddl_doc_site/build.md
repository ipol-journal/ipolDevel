# The *build* section
The build section is a set of one or more sets, each one providing information to obtain and compile the source codes needed for a given demo. If the demo needs to compile several files from different links, the build sets must be indexed as build1, build2,..., build*n* being *n* the total number of builds (see the example below). It is mandatory to write at least build1. If a demo needs to make use of a python package in order to execute the user will have to specify the requirements.txt file location inside the source binary compressed file. Three steps are needed to build a demo:

- Download the original sources codes (with optional userid and password for private demos);

- Build the executables after the download;

- Copy the needed files in a run context to execute the demo.

| key | **description** | **req** |
|:---|:---|:--:|
| url | Link to download the source codes as a compressed file. | yes |
| username | Username for private demos. | no |
| password | Password for private demos. | no |
| construct | Shell command needed to compile the downloaded source code. | no |
| move | List of files needed to execute the demo separated with commas (see example below) | yes |
| virtualenv | Creates a python 3 virtualenv to install any needed python package inside the bin folder. | no |

Build fields

#### Example:

In this case, the demo needs to compile from two different compressed files. The DDL uses the *move* statement to copy the obtained files after the compilation into a run context.

``` json
"build": {
    "build1": {
        "url": "http://www.ipol.im/pub/art/2014/82/sift_anatomy_20141201.zip",
        "construct": "cd sift_anatomy_20141201 && make",
        "move": "sift_anatomy_20141201/bin/sift_cli, sift_anatomy_20141201/bin/match_cli"
    },
    "build2":{
        "url": "http://dev.ipol.im/~monasse/orthoPose_1.0.tar.gz",
        "construct": "matlab -nodisplay -nosplash -nodesktop -r \"cd orthoPose_1.0/; mcc -m mainPoseEstimation.m -a lib/; exit;\"",
        "move": "orthoPose_1.0/mainPoseEstimation, orthoPose_1.0/run_mainPoseEstimation.sh"
        "virtualenv": "sift_anatomy_20141201/requirements.txt"
    }
}
```
