# Introduction
The Demo Description Lines (DDL) define an abstract syntax, written in JSON (JavaScript Object Notation) format, that specifies the IPOL demos. Their main objective is to simplify as much as possible the creation of demos by describing them without the need of writing Python or HTML. This allows fast demo editing in the journal. The following sections describe each of the main keys of the DDL:

- *general*: general options (required);

- *build*: download and compile the source code (required);

- *inputs*: description of the inputs (optional);

- *params*: description of the parameters and user control (optional);

- *run*: script or binary which needs to be called for the execution, along with its parameters (required);

- *archive*: which parameters and files will be stored in the archive (optional);

- *results*: which elements will be displayed as results (required).

The IPOL control panel provides a JSON editor with a simple validator. Most of the syntax errors are detected in real time and reported by this graphical tool.
