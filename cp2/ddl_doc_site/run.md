# The *run* section
The *run* section specifies which script or binary needs to be called to run a demo, along with its parameters. The input files defined in the *input* section are available as arguments with a normalized name input\_{0..n}.{extension} (ex: input_0.png). The parameters define in *params* section are available by their id with \$ as a prefix (ex: "id": "width", \$width).

In this example, the demo is executed by the binary file jpegblocks (compiled and moved in the *build* section), with input_0.png as an input and \$block_size as a parameter.

``` json
"run": "jpegblocks input_0.png $block_size"
```

The execution is then passed to the *run.sh* script, provided in the optional demoextras.zip, with input_0.png \$width as arguments.

``` json
"run": "${demoextras}/run.sh input_0.png $width"
```

In addition, there are other variables that will be substituted before execution (run section). As shown before, to use a variable just insert the name of the variable between curly brackets preceded by a dollar sign.

In the previous example the demoExtras path will be replaced in order that the run section executes a script inside the demoExtras folder. It follows a list of all available variables for the run section:

- **demoextras**: will be replaced by the demoExtras’ path of the current demo,

- **matlab_path**: will be replaced by the path to the current MATLAB installation,

- **bin**: will be replaced by the directory with the compiled code, or any moved element,

- **virtualenv**: will be replaced by the path to the virtualenv, if any. This folder contains the scripts needed to activate the virtualenv.
