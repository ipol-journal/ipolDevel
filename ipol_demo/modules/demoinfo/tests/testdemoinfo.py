# -*- coding:utf-8 -*-
import unittest
import sys
import os
import json
from os import path
import urllib
import datetime
import requests


sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from demoinfo import DemoInfo
from tools import is_json

__author__ = 'josearrecio'

CONFIGFILE = "./testdemoinfo.conf"
DBNAME= "testdemoinfo.db"

# run with
# ../tests$ python -m unittest discover

# Example of demojson
#http://www.freeformatter.com/json-formatter.


####################
# DEMO DESCP JSONS #
####################
#in js true and falses difer from python
false = False
true  = True
json81 = {"general":{"demo_title":"A Survey of Gaussian Convolution Algorithms","input_description":"","param_description":[""],"is_test":false,"xlink_article":"http://www.ipol.im/pub/art/2013/87/"},"build":[{"build_type":"make","url":"http://www.ipol.im/pub/art/2013/87/gaussian_20131215.tgz","srcdir":"gaussian_20131215","binaries":[[".","gaussian_demo"],[".","imdiff"]],"flags":"-j4  --makefile=makefile.gcc"}],"inputs":[{"type":"image","description":"input","max_pixels":"700 * 700","max_weight":"10 * 1024 * 1024","dtype":"3x8i","ext":".png"}],"params":[{"id":"sigma","type":"range","label":"<i>&sigma;<\/i>, Gaussian standard deviation","values":{"min":0.5,"max":30,"step":0.01,"default":5}},{"id":"algo","type":"checkboxes","label":"Algorithms","values":[{"fir":"FIR, <i>tol<\/i>=10<sup>&minus;2<\/sup>"},{"dct":"DCT"},{"box_3":"Box, <i>K<\/i>=3","box_4":"Box, <i>K<\/i>=4","box_5":"Box, <i>K<\/i>=5"},{"ebox_3":"Extended box, <i>K<\/i>=3","ebox_4":"Extended box, <i>K<\/i>=4","ebox_5":"Extended box, <i>K<\/i>=5"},{"sii_3":"SII, <i>K<\/i>=3","sii_4":"SII, <i>K<\/i>=4","sii_5":"SII, <i>K<\/i>=5"},{},{"am_3":"Alvarez&ndash;Mazorra, <i>K<\/i>=3","am_4":"Alvarez&ndash;Mazorra, <i>K<\/i>=4","am_5":"Alvarez&ndash;Mazorra, <i>K<\/i>=5"},{"deriche_2":"Deriche, <i>K<\/i>=2","deriche_3":"Deriche, <i>K<\/i>=3","deriche_4":"Deriche, <i>K<\/i>=4"},{"vyv_3":"Vliet&ndash;Young&ndash;Verbeek, <i>K<\/i>=3","vyv_4":"Vliet&ndash;Young&ndash;Verbeek, <i>K<\/i>=4","vyv_5":"Vliet&ndash;Young&ndash;Verbeek, <i>K<\/i>=5"}],"default":["fir","dct"]}],"run":["run_algorithms.py"],"archive":{"files":{"input_0.orig.png":"uploaded image","input_0.sel.png":"selected subimage","output-fir.png":"output fir","output-dct.png":"output dct","output-box_3.png":"output box_3","output-box_4.png":"output box_4","output-box_5.png":"output box_5","output-ebox_3.png":"output ebox_3","output-ebox_4.png":"output ebox_4","output-ebox_5.png":"output ebox_5","output-sii_3.png":"output sii_3","output-sii_4.png":"output sii_4","output-sii_5.png":"output sii_5","output-am_3.png":"output am_3","output-am_4.png":"output am_4","output-am_5.png":"output am_5","output-deriche_2.png":"output deriche_2","output-deriche_3.png":"output deriche_3","output-deriche_4.png":"output deriche_4","output-vyv_3.png":"output vyv_3","output-vyv_4.png":"output vyv_4","output-vyv_5.png":"output vyv_5"},"params":["sigma","fir","dct","box_3","box_4","box_5","ebox_3","ebox_4","ebox_5","sii_3","sii_4","sii_5","am_3","am_4","am_5","deriche_2","deriche_3","deriche_4","vyv_3","vyv_4","vyv_5"]},"config":{"info_from_file":{"metrics_fir":"metrics_fir.txt","metrics_dct":"metrics_dct.txt","metrics_box_3":"metrics_box_3.txt","metrics_box_4":"metrics_box_4.txt","metrics_box_5":"metrics_box_5.txt","metrics_ebox_3":"metrics_ebox_3.txt","metrics_ebox_4":"metrics_ebox_4.txt","metrics_ebox_5":"metrics_ebox_5.txt","metrics_sii_3":"metrics_sii_3.txt","metrics_sii_4":"metrics_sii_4.txt","metrics_sii_5":"metrics_sii_5.txt","metrics_am_3":"metrics_am_3.txt","metrics_am_4":"metrics_am_4.txt","metrics_am_5":"metrics_am_5.txt","metrics_deriche_2":"metrics_deriche_2.txt","metrics_deriche_3":"metrics_deriche_3.txt","metrics_deriche_4":"metrics_deriche_4.txt","metrics_vyv_3":"metrics_vyv_3.txt","metrics_vyv_4":"metrics_vyv_4.txt","metrics_vyv_5":"metrics_vyv_5.txt"}},"results":[{"type":"gallery","label":"Images:","contents":{"Input":"input_0.sel.png","FIR, <i>tol<\/i>=10<sup>&minus;2<\/sup>":"output-fir.png","DCT":"output-dct.png","Box, <i>K<\/i>=3":"output-box_3.png","Box, <i>K<\/i>=4":"output-box_4.png","Box, <i>K<\/i>=5":"output-box_5.png","Extended box, <i>K<\/i>=3":"output-ebox_3.png","Extended box, <i>K<\/i>=4":"output-ebox_4.png","Extended box, <i>K<\/i>=5":"output-ebox_5.png","SII, <i>K<\/i>=3":"output-sii_3.png","SII, <i>K<\/i>=4":"output-sii_4.png","SII, <i>K<\/i>=5":"output-sii_5.png","Alvarez&ndash;Mazorra, <i>K<\/i>=3":"output-am_3.png","Alvarez&ndash;Mazorra, <i>K<\/i>=4":"output-am_4.png","Alvarez&ndash;Mazorra, <i>K<\/i>=5":"output-am_5.png","Deriche, <i>K<\/i>=2":"output-deriche_2.png","Deriche, <i>K<\/i>=3":"output-deriche_3.png","Deriche, <i>K<\/i>=4":"output-deriche_4.png","Vliet&ndash;Young&ndash;Verbeek, <i>K<\/i>=3":"output-vyv_3.png","Vliet&ndash;Young&ndash;Verbeek, <i>K<\/i>=4":"output-vyv_4.png","Vliet&ndash;Young&ndash;Verbeek, <i>K<\/i>=5":"output-vyv_5.png","Exact*":"output-exact.png"},"style":"height:{{sizeY*ZoomFactor}}px"},{"type":"html_text","contents":["<p style='font-size:85%'>* &ldquo;Exact&rdquo; is computed with FIR, ","<i>tol<\/i>=10<sup>&minus;15<\/sup>, for &sigma;&nbsp;&le;&nbsp;2 and ","DCT for &sigma;&nbsp;&gt;&nbsp;2 ","(using {{params.sigma<=2?'FIR':'DCT'}} for this experiment).<\/p>"]},{"type":"html_text","contents":["<h2>Accuracy<\/h2>","<table style='margin:0px;margin-top:10px;text-align:center'>","<tr>","<th>Method<\/th>","<th>&nbsp;Max Diff&nbsp;<\/th>","<th>&nbsp;RMSE&nbsp;<\/th>","<th>&nbsp;PSNR&nbsp;<\/th>","<\/tr>","<tr ng-repeat='(k,v) in info' ng-if='k.indexOf(\"metrics_\")>-1'","ng-init='alg={ \"fir\":\"FIR, <i>tol<\/i>=10<sup>&minus;2<\/sup>\", \"dct\":\"DCT\", \"box\":\"Box\", \"ebox\":\"Extended box\", \"sii\":\"SII\", \"deriche\":\"Deriche\" , \"vyv\":\"Vliet&ndash;Young&ndash;Verbeek\", \"am\":\"Alvarez&ndash;Mazorra\" }'>","<td>","<span ng-bind-html=\"alg[k.substr(8).split('_')[0]]\"> <\/span>","<span ng-if=\"k.substr(8).split('_').length>1\">",", <i>K<\/i>= {{k.substr(8).split('_')[1]}}","<\/span>","<\/td>","<td> {{v.split('|')[0].split(':')[1]}} <\/td>","<td> {{v.split('|')[1].split(':')[1]}} <\/td>","<td> {{v.split('|')[2].split(':')[1]}} <\/td>","<\/tr>","<\/table>"]}]}
json_g_roussos_diffusion_interpolation = {"general":{"demo_title":"Roussos-Maragos Tensor-Driven Diffusion for Image Interpolation","input_description":["<p>","The image interpolation method by Roussos and Maragos using a ","tensor-driven diffusion equation.","<\/p>"],"param_description":"","enable_crop":true,"crop_maxsize":"{{Math.floor(800/demo.params[0].value)*display_ratio}}","is_test":false,"xlink_article":"http://www.ipol.im/pub/art/2011/g_rmdi/"},"build":[{"build_type":"make","url":"http://www.ipol.im/pub/art/2011/g_rmdi/src.tar.gz","srcdir":"tdinterp-src","prepare_make":"sed -i -e 's/$(LDFLAGS) $(TDINTERP_OBJECTS) -o $@/$(TDINTERP_OBJECTS) -o $@ $(LDFLAGS)/g' -e 's/$(LDFLAGS) $(IMCOARSEN_OBJECTS) -o $@/$(IMCOARSEN_OBJECTS) -o $@ $(LDFLAGS)/g'  -e 's/$(LDFLAGS) $(IMDIFF_OBJECTS) -o $@/$(IMDIFF_OBJECTS) -o $@ $(LDFLAGS)/g' -e 's/$(LDFLAGS) $(NNINTERP_OBJECTS) -o $@/$(NNINTERP_OBJECTS) -o $@ $(LDFLAGS)/g' makefile.gcc ","binaries":[[".","tdinterp"],[".","imcoarsen"],[".","imdiff"],[".","nninterp"]],"flags":"-j --makefile=makefile.gcc"}],"inputs":[{"type":"image","description":"input","max_pixels":1048576,"max_weight":"3 * 1024 * 1024","dtype":"3x8i","ext":".png"}],"params":[{"id":"scalefactor","type":"range","label":["<b>Scale factor.<\/b>"," Determines the dimensions of the interpolated image:"," for example, interpolation with scale factor of 4 increases a ","100&times;100 image to 400&times;400."],"values":{"min":2,"max":6,"step":1,"default":4}},{"id":"maxdim","type":"readonly","label":["<b>Maximal allowed input dimension<\/b>"," input image is constrained in both width and height to limit computation time, so that maximal scaled image is 800&times;800."],"value_expr":["{{Math.floor(800/demo.params[0].value)}}"]},{"id":"psfsigma","type":"range","label":["<b>Deconvolution strength&nbsp;<i>&sigma;<sub>h<\/sub><\/i>.<\/b>"," The interpolation finds an image satisfying the degradation model"," <span style='color:blue'><i>input<\/i>&nbsp;=&nbsp;&darr;","(<i>h<\/i>&nbsp;&lowast;&nbsp;<i>interpolation<\/i>)","<\/span>, "," where &darr;(&sdot;) denotes subsampling and <i>h<\/i> is a Gaussian ","with standard deviation <i>&sigma;<sub>h<\/sub><\/i> in units of ","input pixels.  The <i>&sigma;<sub>h<\/sub><\/i> parameter ","controls the deconvolution stength of the interpolation.  Set ","<i>&sigma;<sub>h<\/sub><\/i>&nbsp;=&nbsp;0 ","for no deconvolution."],"values":{"min":0.15,"max":0.75,"step":0.01,"default":0.35}},{"id":"run_mode","type":"selection_collapsed","label":["<b>&nbsp;The algorithm can run in two different ways:<\/b><br/>","<div style='float:left; text-align:center; padding-bottom:15px; ","padding-left:50px; padding-right:50px'>","<img src='http://www.ipol.im/pub/algo/g_image_interpolation_with_contour_stencils/demo-1.png' ","width='109' height='55' style='padding-bottom:25px' alt='' /><br />","<i>Interpolate image<\/i>","<\/div>","<div style='float:left; text-align:center;'>","<img src='http://www.ipol.im/pub/algo/g_image_interpolation_with_contour_stencils/demo-2.png' width='148' height='80' alt='' /><br />","<i>Coarsen, interpolate, and compare<\/i>","<\/div>","<div style='clear:both'>","<b>Interpolate image<\/b> directly interpolates the selected image.","With <b>Coarsen, interpolate, and compare<\/b> the image is ","coarsened to create the input image according to <i>input<\/i>&nbsp;=&nbsp;&darr;","(<i>h<\/i>&nbsp;&lowast;&nbsp;<i>original<\/i>).The coarsened image is ","then interpolated and compared with the original image.","<\/div>"],"values":{"Interpolate image":"Interpolate","Coarsen, interpolate, and compare":"Coarsen_interpolate_compare"},"default_value":"Interpolate"}],"run":["python:sizeX=x1-x0","python:sizeY=y1-y0",["run_mode=='Interpolate'","echo 'If the image dimensions are small, zoom the displayed results.'","python:displayzoom = int(math.ceil(400.0/(scalefactor*max(sizeX, sizeY))))","echo 'Perform the actual contour stencil interpolation'","tdinterp -x $scalefactor -p $psfsigma  input_0.sel.png interpolated.png >stdout.txt","echo 'Interpolate with Fourier'","tdinterp -N0 -x $scalefactor -p $psfsigma input_0.sel.png fourier.png >>stdout.txt","echo 'For display, create a nearest neighbor zoomed version of the input'","nninterp -g centered -x ${scalefactor*displayzoom} input_0.sel.png input_0_zoom.png >>stdout.txt","nninterp -g centered -x $displayzoom interpolated.png interpolated_zoom.png >>stdout.txt","nninterp -g centered -x $displayzoom fourier.png fourier_zoom.png >>stdout.txt"],["run_mode=='Coarsen_interpolate_compare'","echo 'If the image dimensions are small, zoom the displayed results.'","python:displayzoom = int(math.ceil(350.0/max(sizeX, sizeY)))","echo 'Coarsen the image'","imcoarsen -g topleft -x $scalefactor -p $psfsigma  input_0.sel.png coarsened.png >stdout.txt","nninterp -g centered -x $displayzoom input_0.sel.png input_0.sel_zoom.png >>stdout.txt","echo 'Perform the actual interpolation'","tdinterp  -x $scalefactor -p $psfsigma coarsened.png interpolated.png >>stdout.txt","echo 'Interpolate with Fourier'","tdinterp -N0 -x $scalefactor -p $psfsigma coarsened.png fourier.png >>stdout.txt","echo 'For display, create a nearest neighbor zoomed version of the coarsened image'","nninterp -g topleft -x $scalefactor coarsened.png coarsened_zoom.png >>stdout.txt","echo 'Ensure same size'","python:img=image(self.work_dir+'coarsened_zoom.png')","python:if (sizeX,sizeY)!= img.size: img.crop((0,0,sizeX,sizeY));img.save(self.work_dir+'coarsened_zoom.png')","python:img=image(self.work_dir+'interpolated.png')","python:if (sizeX,sizeY)!= img.size: img.crop((0,0,sizeX,sizeY));img.save(self.work_dir+'interpolated.png')","python:img=image(self.work_dir+'fourier.png')","python:if (sizeX,sizeY)!= img.size: img.crop((0,0,sizeX,sizeY));img.save(self.work_dir+'fourier.png')","echo 'Generate difference image'","imdiff input_0.sel.png interpolated.png  difference.png","imdiff input_0.sel.png fourier.png       fdifference.png","echo 'Compute maximum difference, PSNR, and MSSIM'","imdiff input_0.sel.png interpolated.png >>stdout.txt","nninterp -g centered -x $displayzoom coarsened_zoom.png  coarsened_zoom.png >>stdout.txt","nninterp -g centered -x $displayzoom interpolated.png    interpolated_zoom.png >>stdout.txt","nninterp -g centered -x $displayzoom fourier.png         fourier_zoom.png >>stdout.txt","nninterp -g centered -x $displayzoom difference.png      difference_zoom.png >>stdout.txt","nninterp -g centered -x $displayzoom fdifference.png     fdifference_zoom.png >>stdout.txt"]],"archive":{"files":{"input_0.png":"input","input_0.sel.png":"selected subimage","interpolated.png":"Roussos-Maragos interpolation","fourier.png":"Fourier interpolation","difference.png":"Difference image"},"params":["scalefactor","psfsigma","run_mode"]},"results":[{"type":"file_download","label":"<h2>Download<h2>","contents":{"input":"input_0.sel.png","coarsened":"coarsened.png","Fourier":"fourier.png","Roussos-Maragos":"interpolated.png","exact":"input_0.sel.png","Fourier difference":"fdifference.png","Roussos-Maragos difference":"difference.png"}},{"type":"gallery","label":"<h2>Resulting images<\/h2>","contents":{"Input":"input_0_zoom.png","Coarsened":"coarsened_zoom.png","Fourier {{params['scalefactor']}}&times;":"fourier_zoom.png","Roussos-Maragos {{params['scalefactor']}}&times;":"interpolated_zoom.png","Exact":"input_0.sel_zoom.png","Fourier Difference":"fdifference_zoom.png","Roussos-Maragos Difference":"difference_zoom.png"},"style":"height:{{Math.max(200,sizeY*ZoomFactor)}}px"},{"type":"text_file","label":"<h2>Output<h2>","contents":"stdout.txt","style":"width:40em;height:16em;background-color:#eee"}]}
#json44 = {"general":{"demo_title":"An Implementation of Combined Local-Global Optical Flow","input_description":"Please select or upload the image pair to rectify. Both images must have the same size.","param_description":["You can now run the rectification process."],"enable_crop":false,"is_test":false,"xlink_article":"http://www.ipol.im/pub/art/2015/44/","input_condition":["(input0_size_x==input1_size_x)and(input0_size_y==input1_size_y)","badparams","The images must have the same size"],"thumbnail_size":64},"build":[{"build_type":"cmake","url":"http://www.ipol.im/pub/art/2015/44/clg_6.1.tgz","srcdir":"clg_6.1","binaries":[["../bin","test_clgof"]],"flags":"-j4"},{"build_type":"make","url":"http://www.ipol.im/pub/art/2013/20/imscript_dec2011.tar.gz","srcdir":"imscript","binaries":[[".","bin/"]],"flags":"-j CFLAGS=-O3 IIOFLAGS='-lpng -ltiff -ljpeg -lm'"}],"inputs":[{"type":"image","description":"I1","max_pixels":"1024 * 1024","max_weight":5242880,"dtype":"3x8i","ext":".png"},{"type":"image","description":"I2","max_pixels":"1024 * 1024","max_weight":5242880,"dtype":"3x8i","ext":".png"},{"type":"flow","description":"Ground truth","max_weight":5242880,"dtype":"3x8i","ext":".tiff","required":false}],"params":[{"id":"alpha","type":"range","label":" &alpha; : global regularization parameter (&alpha;>0. Higher values produce more homogeneus fields, &nbsp; lower values allow more variating displacement vectors in a given image region)","values":{"min":0.1,"max":100,"step":0.1,"default":15}},{"id":"rho","type":"range","label":" &rho; : neighborhood size in local approach (size of Gaussian kernel = 2 &rho; + 1, &nbsp; &rho; = 0 implies no local smoothing)","values":{"min":0.1,"max":100,"step":0.1,"default":10}},{"id":"sigma","type":"range","label":" &sigma; : Pre-processing Gaussian smoothing variance","values":{"min":0.3,"max":10,"step":0.01,"default":0.85}}],"run":["ln -fs input_0.png  a.png ","ln -fs input_1.png  b.png ","ln -fs input_2.tiff t.tiff","run_clg_noview.sh $alpha $rho $sigma 1000 1.9 10 0.65 1 0 >stdout.txt","view_clg.sh ipoln  1","view_clg.sh ipol   1","view_clg.sh mid    1","view_clg.sh arrows 1"],"archive":{"files":{"input_0.png":"input #1","input_1.png":"input #2","input_2.tiff":"ground truth","stuff_clg.tiff":"flow","stuff_clg.png":"flow as RGB image"},"params":["alpha","rho","sigma"]},"config":{"info_from_file":{"sixerrors":"sixerror_clg.txt"}},"results":[{"type":"html_text","contents":["<table style='margin-left:0px;margin-right:auto'>","<tr>","<td>","<label> Color-coding of vectors: <\/label>","<select ng-model=\"display.param1\" ng-init=\"display.param1='ipoln'\">","<option ng-repeat=\"scheme in ['ipoln','ipol','mid','arrows']\" value=\"{{scheme}}\">","{{scheme}}","<\/option>","<\/select><br/>","<\/td>","<td>","<img style=\"\" ng-src=\"{{work_url}}/cw.{{display.param1}}.1.png\" />","<\/td>","<\/tr>","<table>"]},{"type":"gallery","label":"<h2>Images<\/h2>","contents":{"Optical flow ":"stuff_clg.{{display.param1}}.1.png","Ground truth":"t.{{display.param1}}.1.png","|flow|":"stuff_clg_abs.png","I<sub>0<\/sub>":"input_0.png","I<sub>1<\/sub>":"input_1.png","div(flow)":"stuff_clg_div.png","grad(flow)":"stuff_clg_grad.png","Warped I<sub>1<\/sub>":"stuff_clg_inv.png","Warped difference":"stuff_clg_aminv.png","Warped average":"stuff_clg_apinv.png","Endpoint error":"stuff_clg_fmt.{{display.param1}}.1.png","Angular error":"stuff_clg_aerr.png"},"style":"height:{{Math.max(sizeY*ZoomFactor,350)}}px"},{"type":"html_text","contents":["<h2>Summary<\/h2>","<div>","<table border='1' cellpadding='6' cellspacing='0' style='margin-left:0px;margin-right:auto'>","<tr bgcolor='#cccccc'>","<td ><\/td>","<th >Running time<\/th>","<th >Average Backprojection Error<\/th>","<th >Average Endpoint Error<\/th>","<th >Average Angular Error<\/th>","<\/tr>","<tr>","<th bgcolor='#cccccc'>clg<\/th>","<td align='center'>{{info.run_time | number:2 }} s<\/td>","<td align='center'>{{info.sixerrors.split(' ')[0]}} <i style='font-size:x-small'>gray levels<\/i><\/td>","<td align='center'>{{info.sixerrors.split(' ')[2]}} <i style='font-size:x-small'>pixels<\/i><\/td>","<td align='center'>{{info.sixerrors.split(' ')[4]}}&nbsp;º<\/td>","<\/tr>","<\/table>","<\/div>"]},{"type":"file_download","label":"<h3>Download inputs:<\/h3>","contents":{"first image I1":"input_0.png","second image I2":"input_1.png","ground truth":"input_2.tiff"}},{"type":"file_download","label":"<h3>Download computed optical flow:<\/h3>","contents":{"tiff":"stuff_tvl1.tiff","flo":"stuff_tvl1.flo","uv":"stuff_tvl1.uv"}},{"type":"html_text","contents":["<p style='font-size:small'>Note on formats:","<ul style='font-size:small'>","<li>The <tt>.tiff<\/tt> file is a two-channel image with floating-point samples.<\/li>","<li>The <tt>.flo<\/tt> file is the same fomat as in the","<a href = 'http://vision.middlebury.edu/flow/code/flow-code/README.txt'>","Middlebury database","<\/a>.<\/li>","<li>The <tt>.uv<\/tt> file can be read and written by ","<a href='http://dev.ipol.im/~coco/file_uv.h'>simple<\/a> code.<\/li>","<\/ul><\/p>"]}]}
json44={ 
  "general": { 
	"demo_title"            :  "An Implementation of Combined Local-Global Optical Flow",
	"input_description"     : "Please select or upload the image pair to rectify. Both images must have the same size.",
	"param_description"     : ["You can now run the rectification process."],
	"enable_crop"           : false,
	"is_test"               : false,
	"xlink_article"         : "http://www.ipol.im/pub/art/2015/44/",
	"input_condition"       : [ "(input0_size_x==input1_size_x)and(input0_size_y==input1_size_y)",
								"badparams",
								"The images must have the same size" ],
	"thumbnail_size"        : 64
  },
  "build":
	[
	  {
		"build_type"    : "cmake",
		"url"           : "http://www.ipol.im/pub/art/2015/44/clg_6.1.tgz",
		"srcdir"        : "clg_6.1",
		"binaries"      : [ ["../bin","test_clgof"] ],
		"flags"         : "-j4"
	  },
	  {
		"build_type"    : "make",
		"url"           : "http://www.ipol.im/pub/art/2013/20/imscript_dec2011.tar.gz",
		"srcdir"        : "imscript",
		"binaries"      : [ [".","bin/"] ],
	   "flags"         : "-j CFLAGS=-O3 IIOFLAGS='-lpng -ltiff -ljpeg -lm'"
	  }
	]
  ,
  "inputs": [ 
	  {
		  "type"            : "image",
		  "description"     : "I1",
		  "max_pixels"      : "1024 * 1024",
		  "max_weight"      : 5242880,
		  "dtype"           : "3x8i",
		  "ext"             : ".png"
	  },
	  {
		  "type"            : "image",
		  "description"     : "I2",
		  "max_pixels"      : "1024 * 1024",
		  "max_weight"      : 5242880,
		  "dtype"           : "3x8i",
		  "ext"             : ".png"
	  },
	  {
		  "type"              : "flow",
		  "description"       : "Ground truth",
		  "ext"               : ".tiff",
		  "required"          : false
	  }
	],
  "params": 
	[
	  {
		"id"            : "alpha",
		"type"          : "range",
		"label"         : " &alpha; : global regularization parameter (&alpha;>0. Higher values produce more homogeneus fields, &nbsp; lower values allow more variating displacement vectors in a given image region)",
		"values"        : { "min":0.1, "max":100, "step":0.1, "default": 15 }
	  }
	  ,
	  {
		"id"            : "rho",
		"type"          : "range",
		"label"         : " &rho; : neighborhood size in local approach (size of Gaussian kernel = 2 &rho; + 1, &nbsp; &rho; = 0 implies no local smoothing)",
		"values"        : { "min":0.1, "max":100, "step":0.1, "default": 10 }
	  }
	  ,
	  {
		"id"            : "sigma",
		"type"          : "range",
		"label"         : " &sigma; : Pre-processing Gaussian smoothing variance",
		"values"        : { "min":0.3, "max":10, "step":0.01, "default": 0.85 }
	  }
	],
  "run": [
	  "ln -fs input_0.png  a.png ",
	  "ln -fs input_1.png  b.png ",
	  "ln -fs input_2.tiff t.tiff",
	  "run_clg_noview.sh $alpha $rho $sigma 1000 1.9 10 0.65 1 0 >stdout.txt",
	  "view_clg.sh ipoln  1",
	  "view_clg.sh ipol   1",
	  "view_clg.sh mid    1",
	  "view_clg.sh arrows 1"
  ]
  ,
  "archive":
	{
	  "files" : { "input_0.png"             : "input #1",
				  "input_1.png"             : "input #2",
				  "input_2.tiff"            : "ground truth",
				  "stuff_clg.tiff"          : "flow",
				  "stuff_clg.png"           : "flow as RGB image"
				},
	  "params" :  [ "alpha", "rho", "sigma" ]
	},
  "config":
	{
	  "info_from_file": {  "sixerrors" : "sixerror_clg.txt"
						}
	}
  ,
  "results": [
	{
	  "type"          : "html_text",
	  "contents"      : [
		"<table style='margin-left:0px;margin-right:auto'>",
		"<tr>",
		  "<td>",
			"<label> Color-coding of vectors: </label>",
			"<select ng-model=\"display.param1\" ng-init=\"display.param1='ipoln'\">",
			  "<option ng-repeat=\"scheme in ['ipoln','ipol','mid','arrows']\" value=\"{{scheme}}\">",
			  "{{scheme}}",
			  "</option>",
			"</select><br/>",
		  "</td>",
		  "<td>",
			"<img style=\"\" ng-src=\"{{work_url}}/cw.{{display.param1}}.1.png\" />",
		  "</td>",
		"</tr>",
		"<table>"
	  ]
	},
	{
	  "type"          : "gallery",
	  "label"         : "<h2>Images</h2>",
	  "contents"      : {   "Optical flow "       : "stuff_clg.{{display.param1}}.1.png",
							"Ground truth"        : "t.{{display.param1}}.1.png" ,
							"|flow|"              : "stuff_clg_abs.png" ,
							"I<sub>0</sub>"       : "input_0.png" ,
							"I<sub>1</sub>"       : "input_1.png" ,
							"div(flow)"           : "stuff_clg_div.png",
							"grad(flow)"          : "stuff_clg_grad.png",
							"Warped I<sub>1</sub>": "stuff_clg_inv.png",
							"Warped difference"   : "stuff_clg_aminv.png" ,
							"Warped average"      : "stuff_clg_apinv.png" ,
							"Endpoint error"      : "stuff_clg_fmt.{{display.param1}}.1.png",
							"Angular error"       : "stuff_clg_aerr.png"
						},
	  "style"         : "height:{{Math.max(sizeY*ZoomFactor,350)}}px"
	},
	{
	  "type"          : "html_text",
	  "contents"      : [
		  "<h2>Summary</h2>",
		  "<div>",
		  "<table border='1' cellpadding='6' cellspacing='0' style='margin-left:0px;margin-right:auto'>",
		  "<tr bgcolor='#cccccc'>",
			"<td ></td>",
			"<th >Running time</th>",
			"<th >Average Backprojection Error</th>",
			"<th >Average Endpoint Error</th>",
			"<th >Average Angular Error</th>",
		  "</tr>",
		  "<tr>",
			"<th bgcolor='#cccccc'>clg</th>",
			"<td align='center'>{{info.run_time | number:2 }} s</td>",
			"<td align='center'>{{info.sixerrors.split(' ')[0]}} <i style='font-size:x-small'>gray levels</i></td>",
			"<td align='center'>{{info.sixerrors.split(' ')[2]}} <i style='font-size:x-small'>pixels</i></td>",
			"<td align='center'>{{info.sixerrors.split(' ')[4]}}&nbsp;º</td>",
		  "</tr>",
		  "</table>",
		  "</div>"
		]
	},
	{
	  "type"          : "file_download",
	  "label"         : "<h3>Download inputs:</h3>",
	  "contents"      : { "first image I1"  : "input_0.png",
						  "second image I2" : "input_1.png",
						  "ground truth"    : "input_2.tiff"
						}
	},
	{
	  "type"          : "file_download",
	  "label"         : "<h3>Download computed optical flow:</h3>",
	  "contents"      : { "tiff": "stuff_tvl1.tiff",
						  "flo" : "stuff_tvl1.flo",
						  "uv"  : "stuff_tvl1.uv" }
	},
	{
	  "type"          : "html_text",
	  "contents"      : [
		"<p style='font-size:small'>Note on formats:",
		"<ul style='font-size:small'>",
		  "<li>The <tt>.tiff</tt> file is a two-channel image with floating-point samples.</li>",
		  "<li>The <tt>.flo</tt> file is the same fomat as in the",
			"<a href = 'http://vision.middlebury.edu/flow/code/flow-code/README.txt'>",
			  "Middlebury database",
			"</a>.</li>",
		  "<li>The <tt>.uv</tt> file can be read and written by ",
			"<a href='http://dev.ipol.im/~coco/file_uv.h'>simple</a> code.</li>",
		"</ul></p>"
	  ]
	}
  ]
}

json20={
  "general": {
	"demo_title"            :  "Horn-Schunck Optical Flow with a Multi-Scale Strategy",
	"input_description"     : "Please select or upload the image pair to rectify. Both images must have the same size.",
	"param_description"     : ["You can now run the rectification process."],
	"enable_crop"           : false,
	"is_test"               : false,
	"xlink_article"         : "http://www.ipol.im/pub/art/2013/20/",
	"input_condition"       : [ "(input0_size_x==input1_size_x)and(input0_size_y==input1_size_y)",
								"badparams",
								"The images must have the same size" ],
	"thumbnail_size"        : 64
  },
  "build":
	[
	  {
		"build_type"    : "make",
		"url"           : "http://www.ipol.im/pub/art/2013/20/phs_3.tar.gz",
		"srcdir"        : "phs_3",
		"binaries"      : [ [".","horn_schunck_pyramidal"] ],
		"flags"         : "-j4"
	  },
	  {
		"build_type"    : "make",
		"url"           : "http://www.ipol.im/pub/art/2013/20/imscript_dec2011.tar.gz",
		"srcdir"        : "imscript",
		"binaries"      : [ [".","bin/"] ],
	   "flags"          : "-j CFLAGS=-O3 IIOFLAGS='-lpng -ltiff -ljpeg -lm'"
	  }
	]
  ,
  "inputs": [
	  {
		  "type"            : "image",
		  "description"     : "I1",
		  "max_pixels"      : "1024 * 1024",
		  "max_weight"      : 5242880,
		  "dtype"           : "3x8i",
		  "ext"             : ".png"
	  },
	  {
		  "type"            : "image",
		  "description"     : "I2",
		  "max_pixels"      : "1024 * 1024",
		  "max_weight"      : 5242880,
		  "dtype"           : "3x8i",
		  "ext"             : ".png"
	  },
	  {
		  "type"              : "flow",
		  "description"       : "Ground truth",
		  "ext"               : ".tiff",
		  "required"          : false
	  }
	],
  "params":
	[
	  {
		"id"            : "alpha",
		"type"          : "range",
		"label"         : "Weight of the regularization term, e.g. &alpha;=1 discontinuous flow,  &alpha;=40 smooth flow",
		"values"        : { "min":0.1, "max":100, "step":0.1, "default": 15 }
	  }
	],
  "run": [
	  "cp ../../bin/horn_schunck_pyramidal ../../bin/phs",
	  "run_method_noview.sh 4 $alpha 0.01 150 5 6 0.65 >stdout.txt",
	  "view_method.sh ipoln  1",
	  "view_method.sh ipol   1",
	  "view_method.sh mid    1",
	  "view_method.sh arrows 1",
	  "python:self.algo_meta['hastruth'] = os.path.isfile(self.work_dir+'input_2.tiff')"
  ]
  ,
  "archive":
	{
	  "files" : { "input_0.png"             : "input #1",
				  "input_1.png"             : "input #2",
				  "input_2.tiff"            : "ground truth",
				  "stuff_phs.tiff"          : "flow",
				  "stuff_phs.png"           : "flow as RGB image"
				},
	  "params" :  [ "alpha" ]
	},
  "config":
	{
	  "info_from_file": {  "sixerrors" : "sixerror_phs.txt"
						}
	}
  ,
  "results": [
	{
	  "type"          : "html_text",
	  "contents"      : [
		"<table style='margin-left:0px;margin-right:auto'>",
		"<tr>",
		  "<td>",
			"<label> Color-coding of vectors: </label>",
			"<select ng-model=\"display.param1\" ng-init=\"display.param1='ipoln'\">",
			  "<option ng-repeat=\"scheme in ['ipoln','ipol','mid','arrows']\" value=\"{{scheme}}\">",
			  "{{scheme}}",
			  "</option>",
			"</select><br/>",
		  "</td>",
		  "<td>",
			"<img style=\"\" ng-src=\"{{work_url}}/cw.{{display.param1}}.1.png\" />",
		  "</td>",
		"</tr>",
		"<table>"
	  ]
	},
	{
	  "type"          : "gallery",
	  "label"         : "<h2>Images</h2>",
	  "contents"      :
		{   "Optical flow "                 : "stuff_phs.{{display.param1}}.1.png",
			"meta.hastruth?Ground truth"    : "t.{{display.param1}}.1.png",
			"I1"                            : "input_0.png" ,
			"I2"                            : "input_1.png" ,
			"|flow|"                        : "stuff_phs_abs.png" ,
			"div(flow)"                     : "stuff_phs_div.png",
			"grad(flow)"                    : "stuff_phs_grad.png",
			"Warped I2"                     : "stuff_phs_inv.png",
			"Warped difference"             : "stuff_phs_aminv.png" ,
			"Warped average"                : "stuff_phs_apinv.png" ,
			"meta.hastruth?Endpoint error"  : "stuff_phs_fmt.{{display.param1}}.1.png",
			"meta.hastruth?Angular error"   : "stuff_phs_aerr.png"
		},
	  "style"         : "height:{{Math.max(sizeY*ZoomFactor,350)}}px"
	},
	{
	  "type"          : "html_text",
	  "contents"      : [
		  "<h2>Summary</h2>",
		  "<div>",
		  "<table border='1' cellpadding='6' cellspacing='0' style='margin-left:0px;margin-right:auto'>",
		  "<tr bgcolor='#cccccc'>",
			"<td ></td>",
			"<th >Running time</th>",
			"<th >Average Backprojection Error</th>",
			"<th ng-if='meta.hastruth'>Average Endpoint Error</th>",
			"<th ng-if='meta.hastruth'>Average Angular Error</th>",
		  "</tr>",
		  "<tr>",
			"<th bgcolor='#cccccc'>phs</th>",
			"<td align='center'>{{info.run_time | number:2 }} s</td>",
			"<td align='center'>{{info.sixerrors.split(' ')[0]}} <i style='font-size:x-small'>gray levels</i></td>",
			"<td  ng-if='meta.hastruth' align='center'>{{info.sixerrors.split(' ')[2]}} <i style='font-size:x-small'>pixels</i></td>",
			"<td  ng-if='meta.hastruth' align='center'>{{info.sixerrors.split(' ')[4]}}&nbsp;º</td>",
		  "</tr>",
		  "</table>",
		  "</div>"
		]
	},
	{
	  "type"          : "file_download",
	  "label"         : "<h3>Download inputs:</h3>",
	  "contents"      : { "first image I1"  : "input_0.png",
						  "second image I2" : "input_1.png",
						  "ground truth"    : "input_2.tiff"
						}
	},
	{
	  "type"          : "file_download",
	  "label"         : "<h3>Download computed optical flow:</h3>",
	  "contents"      : { "tiff": "stuff_phs.tiff",
						  "flo" : "stuff_phs.flo",
						  "uv"  : "stuff_phs.uv" }
	},
	{
	  "type"          : "html_text",
	  "contents"      : [
		"<p style='font-size:small'>Note on formats:",
		"<ul style='font-size:small'>",
		  "<li>The <tt>.tiff</tt> file is a two-channel image with floating-point samples.</li>",
		  "<li>The <tt>.flo</tt> file is the same fomat as in the",
			"<a href = 'http://vision.middlebury.edu/flow/code/flow-code/README.txt'>",
			  "Middlebury database",
			"</a>.</li>",
		  "<li>The <tt>.uv</tt> file can be read and written by ",
			"<a href='http://dev.ipol.im/~coco/file_uv.h'>simple</a> code.</li>",
		"</ul></p>"
	  ]
	}
  ]
}
#loqpasoaposter="{'inputs': [{'description': 'input', 'max_pixels': '700 * 700', 'dtype': '3x8i', 'ext': '.png', 'type': 'image', 'max_weight': '10 * 1024 * 1024'}], 'results': [{'style': 'height:{{sizeY*ZoomFactor}}px', 'type': 'gallery', 'contents': {'Input': 'input_0.sel.png', 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=3': 'output-am_3.png', 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=5': 'output-am_5.png', 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=4': 'output-am_4.png', 'DCT': 'output-dct.png', 'FIR, <i>tol<\\\\/i>=10<sup>&minus;2<\\\\/sup>': 'output-fir.png', 'Exact*': 'output-exact.png', 'Box, <i>K<\\\\/i>=3': 'output-box_3.png', 'Box, <i>K<\\\\/i>=4': 'output-box_4.png', 'Box, <i>K<\\\\/i>=5': 'output-box_5.png', 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=5': 'output-vyv_5.png', 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=4': 'output-vyv_4.png', 'Extended box, <i>K<\\\\/i>=3': 'output-ebox_3.png', 'Extended box, <i>K<\\\\/i>=4': 'output-ebox_4.png', 'Extended box, <i>K<\\\\/i>=5': 'output-ebox_5.png', 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=3': 'output-vyv_3.png', 'SII, <i>K<\\\\/i>=3': 'output-sii_3.png', 'SII, <i>K<\\\\/i>=4': 'output-sii_4.png', 'SII, <i>K<\\\\/i>=5': 'output-sii_5.png', 'Deriche, <i>K<\\\\/i>=3': 'output-deriche_3.png', 'Deriche, <i>K<\\\\/i>=2': 'output-deriche_2.png', 'Deriche, <i>K<\\\\/i>=4': 'output-deriche_4.png'}, 'label': 'Images:'}, {'type': 'html_text', 'contents': [\"<p style='font-size:85%'>* &ldquo;Exact&rdquo; is computed with FIR, \", '<i>tol<\\\\/i>=10<sup>&minus;15<\\\\/sup>, for &sigma;&nbsp;&le;&nbsp;2 and ', 'DCT for &sigma;&nbsp;&gt;&nbsp;2 ', \"(using {{params.sigma<=2?'FIR':'DCT'}} for this experiment).<\\\\/p>\"]}, {'type': 'html_text', 'contents': ['<h2>Accuracy<\\\\/h2>', \"<table style='margin:0px;margin-top:10px;text-align:center'>\", '<tr>', '<th>Method<\\\\/th>', '<th>&nbsp;Max Diff&nbsp;<\\\\/th>', '<th>&nbsp;RMSE&nbsp;<\\\\/th>', '<th>&nbsp;PSNR&nbsp;<\\\\/th>', '<\\\\/tr>', '<tr ng-repeat=\\'(k,v) in info\\' ng-if=\\'k.indexOf(\"metrics_\")>-1\\'', 'ng-init=\\'alg={ \"fir\":\"FIR, <i>tol<\\\\/i>=10<sup>&minus;2<\\\\/sup>\", \"dct\":\"DCT\", \"box\":\"Box\", \"ebox\":\"Extended box\", \"sii\":\"SII\", \"deriche\":\"Deriche\" , \"vyv\":\"Vliet&ndash;Young&ndash;Verbeek\", \"am\":\"Alvarez&ndash;Mazorra\" }\\'>', '<td>', '<span ng-bind-html=\"alg[k.substr(8).split(\\'_\\')[0]]\"> <\\\\/span>', '<span ng-if=\"k.substr(8).split(\\'_\\').length>1\">', \", <i>K<\\\\/i>= {{k.substr(8).split('_')[1]}}\", '<\\\\/span>', '<\\\\/td>', \"<td> {{v.split('|')[0].split(':')[1]}} <\\\\/td>\", \"<td> {{v.split('|')[1].split(':')[1]}} <\\\\/td>\", \"<td> {{v.split('|')[2].split(':')[1]}} <\\\\/td>\", '<\\\\/tr>', '<\\\\/table>']}], 'params': [{'values': {'default': 5, 'max': 30, 'step': 0.01, 'min': 0.5}, 'type': 'range', 'id': 'sigma', 'label': '<i>&sigma;<\\\\/i>, Gaussian standard deviation'}, {'default': ['fir', 'dct'], 'values': [{'fir': 'FIR, <i>tol<\\\\/i>=10<sup>&minus;2<\\\\/sup>'}, {'dct': 'DCT'}, {'box_5': 'Box, <i>K<\\\\/i>=5', 'box_4': 'Box, <i>K<\\\\/i>=4', 'box_3': 'Box, <i>K<\\\\/i>=3'}, {'ebox_3': 'Extended box, <i>K<\\\\/i>=3', 'ebox_5': 'Extended box, <i>K<\\\\/i>=5', 'ebox_4': 'Extended box, <i>K<\\\\/i>=4'}, {'sii_3': 'SII, <i>K<\\\\/i>=3', 'sii_5': 'SII, <i>K<\\\\/i>=5', 'sii_4': 'SII, <i>K<\\\\/i>=4'}, {}, {'am_3': 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=3', 'am_5': 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=5', 'am_4': 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=4'}, {'deriche_4': 'Deriche, <i>K<\\\\/i>=4', 'deriche_2': 'Deriche, <i>K<\\\\/i>=2', 'deriche_3': 'Deriche, <i>K<\\\\/i>=3'}, {'vyv_3': 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=3', 'vyv_5': 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=5', 'vyv_4': 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=4'}], 'type': 'checkboxes', 'id': 'algo', 'label': 'Algorithms'}], 'build': [{'url': 'http://www.ipol.im/pub/art/2013/87/gaussian_20131215.tgz', 'srcdir': 'gaussian_20131215', 'binaries': [['.', 'gaussian_demo'], ['.', 'imdiff']], 'flags': '-j4  --makefile=makefile.gcc', 'build_type': 'make'}], 'run': ['run_algorithms.py'], 'config': {'info_from_file': {'metrics_box_3': 'metrics_box_3.txt', 'metrics_box_5': 'metrics_box_5.txt', 'metrics_box_4': 'metrics_box_4.txt', 'metrics_deriche_3': 'metrics_deriche_3.txt', 'metrics_dct': 'metrics_dct.txt', 'metrics_deriche_2': 'metrics_deriche_2.txt', 'metrics_fir': 'metrics_fir.txt', 'metrics_sii_4': 'metrics_sii_4.txt', 'metrics_sii_3': 'metrics_sii_3.txt', 'metrics_am_3': 'metrics_am_3.txt', 'metrics_vyv_3': 'metrics_vyv_3.txt', 'metrics_deriche_4': 'metrics_deriche_4.txt', 'metrics_vyv_5': 'metrics_vyv_5.txt', 'metrics_am_5': 'metrics_am_5.txt', 'metrics_vyv_4': 'metrics_vyv_4.txt', 'metrics_ebox_5': 'metrics_ebox_5.txt', 'metrics_ebox_4': 'metrics_ebox_4.txt', 'metrics_sii_5': 'metrics_sii_5.txt', 'metrics_ebox_3': 'metrics_ebox_3.txt', 'metrics_am_4': 'metrics_am_4.txt'}}, 'archive': {'files': {'output-deriche_2.png': 'output deriche_2', 'output-deriche_3.png': 'output deriche_3', 'output-sii_5.png': 'output sii_5', 'output-ebox_4.png': 'output ebox_4', 'output-am_3.png': 'output am_3', 'output-fir.png': 'output fir', 'output-box_4.png': 'output box_4', 'output-sii_3.png': 'output sii_3', 'output-vyv_5.png': 'output vyv_5', 'output-vyv_4.png': 'output vyv_4', 'output-box_3.png': 'output box_3', 'input_0.orig.png': 'uploaded image', 'output-vyv_3.png': 'output vyv_3', 'output-box_5.png': 'output box_5', 'output-am_5.png': 'output am_5', 'output-am_4.png': 'output am_4', 'input_0.sel.png': 'selected subimage', 'output-dct.png': 'output dct', 'output-deriche_4.png': 'output deriche_4', 'output-ebox_5.png': 'output ebox_5', 'output-sii_4.png': 'output sii_4', 'output-ebox_3.png': 'output ebox_3'}, 'params': ['sigma', 'fir', 'dct', 'box_3', 'box_4', 'box_5', 'ebox_3', 'ebox_4', 'ebox_5', 'sii_3', 'sii_4', 'sii_5', 'am_3', 'am_4', 'am_5', 'deriche_2', 'deriche_3', 'deriche_4', 'vyv_3', 'vyv_4', 'vyv_5']}, 'general': {'demo_title': 'A Survey of Gaussian Convolution Algorithms', 'is_test': 'false', 'xlink_article': 'http://www.ipol.im/pub/art/2013/87/', 'param_description': [''], 'input_description': ''}}"
#json81="{'inputs': [{'description': 'input', 'max_pixels': '700 * 700', 'dtype': '3x8i', 'ext': '.png', 'type': 'image', 'max_weight': '10 * 1024 * 1024'}], 'results': [{'style': 'height:{{sizeY*ZoomFactor}}px', 'type': 'gallery', 'contents': {'Input': 'input_0.sel.png', 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=3': 'output-am_3.png', 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=5': 'output-am_5.png', 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=4': 'output-am_4.png', 'DCT': 'output-dct.png', 'FIR, <i>tol<\\\\/i>=10<sup>&minus;2<\\\\/sup>': 'output-fir.png', 'Exact*': 'output-exact.png', 'Box, <i>K<\\\\/i>=3': 'output-box_3.png', 'Box, <i>K<\\\\/i>=4': 'output-box_4.png', 'Box, <i>K<\\\\/i>=5': 'output-box_5.png', 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=5': 'output-vyv_5.png', 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=4': 'output-vyv_4.png', 'Extended box, <i>K<\\\\/i>=3': 'output-ebox_3.png', 'Extended box, <i>K<\\\\/i>=4': 'output-ebox_4.png', 'Extended box, <i>K<\\\\/i>=5': 'output-ebox_5.png', 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=3': 'output-vyv_3.png', 'SII, <i>K<\\\\/i>=3': 'output-sii_3.png', 'SII, <i>K<\\\\/i>=4': 'output-sii_4.png', 'SII, <i>K<\\\\/i>=5': 'output-sii_5.png', 'Deriche, <i>K<\\\\/i>=3': 'output-deriche_3.png', 'Deriche, <i>K<\\\\/i>=2': 'output-deriche_2.png', 'Deriche, <i>K<\\\\/i>=4': 'output-deriche_4.png'}, 'label': 'Images:'}, {'type': 'html_text', 'contents': [\"<p style='font-size:85%'>* &ldquo;Exact&rdquo; is computed with FIR, \", '<i>tol<\\\\/i>=10<sup>&minus;15<\\\\/sup>, for &sigma;&nbsp;&le;&nbsp;2 and ', 'DCT for &sigma;&nbsp;&gt;&nbsp;2 ', \"(using {{params.sigma<=2?'FIR':'DCT'}} for this experiment).<\\\\/p>\"]}, {'type': 'html_text', 'contents': ['<h2>Accuracy<\\\\/h2>', \"<table style='margin:0px;margin-top:10px;text-align:center'>\", '<tr>', '<th>Method<\\\\/th>', '<th>&nbsp;Max Diff&nbsp;<\\\\/th>', '<th>&nbsp;RMSE&nbsp;<\\\\/th>', '<th>&nbsp;PSNR&nbsp;<\\\\/th>', '<\\\\/tr>', '<tr ng-repeat=\\'(k,v) in info\\' ng-if=\\'k.indexOf(\"metrics_\")>-1\\'', 'ng-init=\\'alg={ \"fir\":\"FIR, <i>tol<\\\\/i>=10<sup>&minus;2<\\\\/sup>\", \"dct\":\"DCT\", \"box\":\"Box\", \"ebox\":\"Extended box\", \"sii\":\"SII\", \"deriche\":\"Deriche\" , \"vyv\":\"Vliet&ndash;Young&ndash;Verbeek\", \"am\":\"Alvarez&ndash;Mazorra\" }\\'>', '<td>', '<span ng-bind-html=\"alg[k.substr(8).split(\\'_\\')[0]]\"> <\\\\/span>', '<span ng-if=\"k.substr(8).split(\\'_\\').length>1\">', \", <i>K<\\\\/i>= {{k.substr(8).split('_')[1]}}\", '<\\\\/span>', '<\\\\/td>', \"<td> {{v.split('|')[0].split(':')[1]}} <\\\\/td>\", \"<td> {{v.split('|')[1].split(':')[1]}} <\\\\/td>\", \"<td> {{v.split('|')[2].split(':')[1]}} <\\\\/td>\", '<\\\\/tr>', '<\\\\/table>']}], 'params': [{'values': {'default': 5, 'max': 30, 'step': 0.01, 'min': 0.5}, 'type': 'range', 'id': 'sigma', 'label': '<i>&sigma;<\\\\/i>, Gaussian standard deviation'}, {'default': ['fir', 'dct'], 'values': [{'fir': 'FIR, <i>tol<\\\\/i>=10<sup>&minus;2<\\\\/sup>'}, {'dct': 'DCT'}, {'box_5': 'Box, <i>K<\\\\/i>=5', 'box_4': 'Box, <i>K<\\\\/i>=4', 'box_3': 'Box, <i>K<\\\\/i>=3'}, {'ebox_3': 'Extended box, <i>K<\\\\/i>=3', 'ebox_5': 'Extended box, <i>K<\\\\/i>=5', 'ebox_4': 'Extended box, <i>K<\\\\/i>=4'}, {'sii_3': 'SII, <i>K<\\\\/i>=3', 'sii_5': 'SII, <i>K<\\\\/i>=5', 'sii_4': 'SII, <i>K<\\\\/i>=4'}, {}, {'am_3': 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=3', 'am_5': 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=5', 'am_4': 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=4'}, {'deriche_4': 'Deriche, <i>K<\\\\/i>=4', 'deriche_2': 'Deriche, <i>K<\\\\/i>=2', 'deriche_3': 'Deriche, <i>K<\\\\/i>=3'}, {'vyv_3': 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=3', 'vyv_5': 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=5', 'vyv_4': 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=4'}], 'type': 'checkboxes', 'id': 'algo', 'label': 'Algorithms'}], 'build': [{'url': 'http://www.ipol.im/pub/art/2013/87/gaussian_20131215.tgz', 'srcdir': 'gaussian_20131215', 'binaries': [['.', 'gaussian_demo'], ['.', 'imdiff']], 'flags': '-j4  --makefile=makefile.gcc', 'build_type': 'make'}], 'run': ['run_algorithms.py'], 'config': {'info_from_file': {'metrics_box_3': 'metrics_box_3.txt', 'metrics_box_5': 'metrics_box_5.txt', 'metrics_box_4': 'metrics_box_4.txt', 'metrics_deriche_3': 'metrics_deriche_3.txt', 'metrics_dct': 'metrics_dct.txt', 'metrics_deriche_2': 'metrics_deriche_2.txt', 'metrics_fir': 'metrics_fir.txt', 'metrics_sii_4': 'metrics_sii_4.txt', 'metrics_sii_3': 'metrics_sii_3.txt', 'metrics_am_3': 'metrics_am_3.txt', 'metrics_vyv_3': 'metrics_vyv_3.txt', 'metrics_deriche_4': 'metrics_deriche_4.txt', 'metrics_vyv_5': 'metrics_vyv_5.txt', 'metrics_am_5': 'metrics_am_5.txt', 'metrics_vyv_4': 'metrics_vyv_4.txt', 'metrics_ebox_5': 'metrics_ebox_5.txt', 'metrics_ebox_4': 'metrics_ebox_4.txt', 'metrics_sii_5': 'metrics_sii_5.txt', 'metrics_ebox_3': 'metrics_ebox_3.txt', 'metrics_am_4': 'metrics_am_4.txt'}}, 'archive': {'files': {'output-deriche_2.png': 'output deriche_2', 'output-deriche_3.png': 'output deriche_3', 'output-sii_5.png': 'output sii_5', 'output-ebox_4.png': 'output ebox_4', 'output-am_3.png': 'output am_3', 'output-fir.png': 'output fir', 'output-box_4.png': 'output box_4', 'output-sii_3.png': 'output sii_3', 'output-vyv_5.png': 'output vyv_5', 'output-vyv_4.png': 'output vyv_4', 'output-box_3.png': 'output box_3', 'input_0.orig.png': 'uploaded image', 'output-vyv_3.png': 'output vyv_3', 'output-box_5.png': 'output box_5', 'output-am_5.png': 'output am_5', 'output-am_4.png': 'output am_4', 'input_0.sel.png': 'selected subimage', 'output-dct.png': 'output dct', 'output-deriche_4.png': 'output deriche_4', 'output-ebox_5.png': 'output ebox_5', 'output-sii_4.png': 'output sii_4', 'output-ebox_3.png': 'output ebox_3'}, 'params': ['sigma', 'fir', 'dct', 'box_3', 'box_4', 'box_5', 'ebox_3', 'ebox_4', 'ebox_5', 'sii_3', 'sii_4', 'sii_5', 'am_3', 'am_4', 'am_5', 'deriche_2', 'deriche_3', 'deriche_4', 'vyv_3', 'vyv_4', 'vyv_5']}, 'general': {'demo_title': 'A Survey of Gaussian Convolution Algorithms', 'is_test': 'false', 'xlink_article': 'http://www.ipol.im/pub/art/2013/87/', 'param_description': [''], 'input_description': ''}}"
emptyjson = {}
demojson_encoded = "%22%7B'inputs'%3A%20%5B%7B'description'%3A%20'input'%2C%20'max_pixels'%3A%20'700%20*%20700'%2C%20'dtype'%3A%20'3x8i'%2C%20'ext'%3A%20'.png'%2C%20'type'%3A%20'image'%2C%20'max_weight'%3A%20'10%20*%201024%20*%201024'%7D%5D%2C%20'results'%3A%20%5B%7B'style'%3A%20'height%3A%7B%7BsizeY*ZoomFactor%7D%7Dpx'%2C%20'type'%3A%20'gallery'%2C%20'contents'%3A%20%7B'Input'%3A%20'input_0.sel.png'%2C%20'Alvarez%26ndash%3BMazorra%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%3A%20'output-am_3.png'%2C%20'Alvarez%26ndash%3BMazorra%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%3A%20'output-am_5.png'%2C%20'Alvarez%26ndash%3BMazorra%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%3A%20'output-am_4.png'%2C%20'DCT'%3A%20'output-dct.png'%2C%20'FIR%2C%20%3Ci%3Etol%3C%5C%5C%5C%5C%2Fi%3E%3D10%3Csup%3E%26minus%3B2%3C%5C%5C%5C%5C%2Fsup%3E'%3A%20'output-fir.png'%2C%20'Exact*'%3A%20'output-exact.png'%2C%20'Box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%3A%20'output-box_3.png'%2C%20'Box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%3A%20'output-box_4.png'%2C%20'Box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%3A%20'output-box_5.png'%2C%20'Vliet%26ndash%3BYoung%26ndash%3BVerbeek%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%3A%20'output-vyv_5.png'%2C%20'Vliet%26ndash%3BYoung%26ndash%3BVerbeek%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%3A%20'output-vyv_4.png'%2C%20'Extended%20box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%3A%20'output-ebox_3.png'%2C%20'Extended%20box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%3A%20'output-ebox_4.png'%2C%20'Extended%20box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%3A%20'output-ebox_5.png'%2C%20'Vliet%26ndash%3BYoung%26ndash%3BVerbeek%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%3A%20'output-vyv_3.png'%2C%20'SII%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%3A%20'output-sii_3.png'%2C%20'SII%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%3A%20'output-sii_4.png'%2C%20'SII%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%3A%20'output-sii_5.png'%2C%20'Deriche%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%3A%20'output-deriche_3.png'%2C%20'Deriche%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D2'%3A%20'output-deriche_2.png'%2C%20'Deriche%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%3A%20'output-deriche_4.png'%7D%2C%20'label'%3A%20'Images%3A'%7D%2C%20%7B'type'%3A%20'html_text'%2C%20'contents'%3A%20%5B%5C%22%3Cp%20style%3D'font-size%3A85%25'%3E*%20%26ldquo%3BExact%26rdquo%3B%20is%20computed%20with%20FIR%2C%20%5C%22%2C%20'%3Ci%3Etol%3C%5C%5C%5C%5C%2Fi%3E%3D10%3Csup%3E%26minus%3B15%3C%5C%5C%5C%5C%2Fsup%3E%2C%20for%20%26sigma%3B%26nbsp%3B%26le%3B%26nbsp%3B2%20and%20'%2C%20'DCT%20for%20%26sigma%3B%26nbsp%3B%26gt%3B%26nbsp%3B2%20'%2C%20%5C%22(using%20%7B%7Bparams.sigma%3C%3D2%3F'FIR'%3A'DCT'%7D%7D%20for%20this%20experiment).%3C%5C%5C%5C%5C%2Fp%3E%5C%22%5D%7D%2C%20%7B'type'%3A%20'html_text'%2C%20'contents'%3A%20%5B'%3Ch2%3EAccuracy%3C%5C%5C%5C%5C%2Fh2%3E'%2C%20%5C%22%3Ctable%20style%3D'margin%3A0px%3Bmargin-top%3A10px%3Btext-align%3Acenter'%3E%5C%22%2C%20'%3Ctr%3E'%2C%20'%3Cth%3EMethod%3C%5C%5C%5C%5C%2Fth%3E'%2C%20'%3Cth%3E%26nbsp%3BMax%20Diff%26nbsp%3B%3C%5C%5C%5C%5C%2Fth%3E'%2C%20'%3Cth%3E%26nbsp%3BRMSE%26nbsp%3B%3C%5C%5C%5C%5C%2Fth%3E'%2C%20'%3Cth%3E%26nbsp%3BPSNR%26nbsp%3B%3C%5C%5C%5C%5C%2Fth%3E'%2C%20'%3C%5C%5C%5C%5C%2Ftr%3E'%2C%20'%3Ctr%20ng-repeat%3D%5C%5C'(k%2Cv)%20in%20info%5C%5C'%20ng-if%3D%5C%5C'k.indexOf(%5C%22metrics_%5C%22)%3E-1%5C%5C''%2C%20'ng-init%3D%5C%5C'alg%3D%7B%20%5C%22fir%5C%22%3A%5C%22FIR%2C%20%3Ci%3Etol%3C%5C%5C%5C%5C%2Fi%3E%3D10%3Csup%3E%26minus%3B2%3C%5C%5C%5C%5C%2Fsup%3E%5C%22%2C%20%5C%22dct%5C%22%3A%5C%22DCT%5C%22%2C%20%5C%22box%5C%22%3A%5C%22Box%5C%22%2C%20%5C%22ebox%5C%22%3A%5C%22Extended%20box%5C%22%2C%20%5C%22sii%5C%22%3A%5C%22SII%5C%22%2C%20%5C%22deriche%5C%22%3A%5C%22Deriche%5C%22%20%2C%20%5C%22vyv%5C%22%3A%5C%22Vliet%26ndash%3BYoung%26ndash%3BVerbeek%5C%22%2C%20%5C%22am%5C%22%3A%5C%22Alvarez%26ndash%3BMazorra%5C%22%20%7D%5C%5C'%3E'%2C%20'%3Ctd%3E'%2C%20'%3Cspan%20ng-bind-html%3D%5C%22alg%5Bk.substr(8).split(%5C%5C'_%5C%5C')%5B0%5D%5D%5C%22%3E%20%3C%5C%5C%5C%5C%2Fspan%3E'%2C%20'%3Cspan%20ng-if%3D%5C%22k.substr(8).split(%5C%5C'_%5C%5C').length%3E1%5C%22%3E'%2C%20%5C%22%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D%20%7B%7Bk.substr(8).split('_')%5B1%5D%7D%7D%5C%22%2C%20'%3C%5C%5C%5C%5C%2Fspan%3E'%2C%20'%3C%5C%5C%5C%5C%2Ftd%3E'%2C%20%5C%22%3Ctd%3E%20%7B%7Bv.split('%7C')%5B0%5D.split('%3A')%5B1%5D%7D%7D%20%3C%5C%5C%5C%5C%2Ftd%3E%5C%22%2C%20%5C%22%3Ctd%3E%20%7B%7Bv.split('%7C')%5B1%5D.split('%3A')%5B1%5D%7D%7D%20%3C%5C%5C%5C%5C%2Ftd%3E%5C%22%2C%20%5C%22%3Ctd%3E%20%7B%7Bv.split('%7C')%5B2%5D.split('%3A')%5B1%5D%7D%7D%20%3C%5C%5C%5C%5C%2Ftd%3E%5C%22%2C%20'%3C%5C%5C%5C%5C%2Ftr%3E'%2C%20'%3C%5C%5C%5C%5C%2Ftable%3E'%5D%7D%5D%2C%20'params'%3A%20%5B%7B'values'%3A%20%7B'default'%3A%205%2C%20'max'%3A%2030%2C%20'step'%3A%200.01%2C%20'min'%3A%200.5%7D%2C%20'type'%3A%20'range'%2C%20'id'%3A%20'sigma'%2C%20'label'%3A%20'%3Ci%3E%26sigma%3B%3C%5C%5C%5C%5C%2Fi%3E%2C%20Gaussian%20standard%20deviation'%7D%2C%20%7B'default'%3A%20%5B'fir'%2C%20'dct'%5D%2C%20'values'%3A%20%5B%7B'fir'%3A%20'FIR%2C%20%3Ci%3Etol%3C%5C%5C%5C%5C%2Fi%3E%3D10%3Csup%3E%26minus%3B2%3C%5C%5C%5C%5C%2Fsup%3E'%7D%2C%20%7B'dct'%3A%20'DCT'%7D%2C%20%7B'box_5'%3A%20'Box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%2C%20'box_4'%3A%20'Box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%2C%20'box_3'%3A%20'Box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%7D%2C%20%7B'ebox_3'%3A%20'Extended%20box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%2C%20'ebox_5'%3A%20'Extended%20box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%2C%20'ebox_4'%3A%20'Extended%20box%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%7D%2C%20%7B'sii_3'%3A%20'SII%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%2C%20'sii_5'%3A%20'SII%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%2C%20'sii_4'%3A%20'SII%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%7D%2C%20%7B%7D%2C%20%7B'am_3'%3A%20'Alvarez%26ndash%3BMazorra%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%2C%20'am_5'%3A%20'Alvarez%26ndash%3BMazorra%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%2C%20'am_4'%3A%20'Alvarez%26ndash%3BMazorra%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%7D%2C%20%7B'deriche_4'%3A%20'Deriche%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%2C%20'deriche_2'%3A%20'Deriche%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D2'%2C%20'deriche_3'%3A%20'Deriche%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%7D%2C%20%7B'vyv_3'%3A%20'Vliet%26ndash%3BYoung%26ndash%3BVerbeek%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D3'%2C%20'vyv_5'%3A%20'Vliet%26ndash%3BYoung%26ndash%3BVerbeek%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D5'%2C%20'vyv_4'%3A%20'Vliet%26ndash%3BYoung%26ndash%3BVerbeek%2C%20%3Ci%3EK%3C%5C%5C%5C%5C%2Fi%3E%3D4'%7D%5D%2C%20'type'%3A%20'checkboxes'%2C%20'id'%3A%20'algo'%2C%20'label'%3A%20'Algorithms'%7D%5D%2C%20'build'%3A%20%5B%7B'url'%3A%20'http%3A%2F%2Fwww.ipol.im%2Fpub%2Fart%2F2013%2F87%2Fgaussian_20131215.tgz'%2C%20'srcdir'%3A%20'gaussian_20131215'%2C%20'binaries'%3A%20%5B%5B'.'%2C%20'gaussian_demo'%5D%2C%20%5B'.'%2C%20'imdiff'%5D%5D%2C%20'flags'%3A%20'-j4%20%20--makefile%3Dmakefile.gcc'%2C%20'build_type'%3A%20'make'%7D%5D%2C%20'run'%3A%20%5B'run_algorithms.py'%5D%2C%20'config'%3A%20%7B'info_from_file'%3A%20%7B'metrics_box_3'%3A%20'metrics_box_3.txt'%2C%20'metrics_box_5'%3A%20'metrics_box_5.txt'%2C%20'metrics_box_4'%3A%20'metrics_box_4.txt'%2C%20'metrics_deriche_3'%3A%20'metrics_deriche_3.txt'%2C%20'metrics_dct'%3A%20'metrics_dct.txt'%2C%20'metrics_deriche_2'%3A%20'metrics_deriche_2.txt'%2C%20'metrics_fir'%3A%20'metrics_fir.txt'%2C%20'metrics_sii_4'%3A%20'metrics_sii_4.txt'%2C%20'metrics_sii_3'%3A%20'metrics_sii_3.txt'%2C%20'metrics_am_3'%3A%20'metrics_am_3.txt'%2C%20'metrics_vyv_3'%3A%20'metrics_vyv_3.txt'%2C%20'metrics_deriche_4'%3A%20'metrics_deriche_4.txt'%2C%20'metrics_vyv_5'%3A%20'metrics_vyv_5.txt'%2C%20'metrics_am_5'%3A%20'metrics_am_5.txt'%2C%20'metrics_vyv_4'%3A%20'metrics_vyv_4.txt'%2C%20'metrics_ebox_5'%3A%20'metrics_ebox_5.txt'%2C%20'metrics_ebox_4'%3A%20'metrics_ebox_4.txt'%2C%20'metrics_sii_5'%3A%20'metrics_sii_5.txt'%2C%20'metrics_ebox_3'%3A%20'metrics_ebox_3.txt'%2C%20'metrics_am_4'%3A%20'metrics_am_4.txt'%7D%7D%2C%20'archive'%3A%20%7B'files'%3A%20%7B'output-deriche_2.png'%3A%20'output%20deriche_2'%2C%20'output-deriche_3.png'%3A%20'output%20deriche_3'%2C%20'output-sii_5.png'%3A%20'output%20sii_5'%2C%20'output-ebox_4.png'%3A%20'output%20ebox_4'%2C%20'output-am_3.png'%3A%20'output%20am_3'%2C%20'output-fir.png'%3A%20'output%20fir'%2C%20'output-box_4.png'%3A%20'output%20box_4'%2C%20'output-sii_3.png'%3A%20'output%20sii_3'%2C%20'output-vyv_5.png'%3A%20'output%20vyv_5'%2C%20'output-vyv_4.png'%3A%20'output%20vyv_4'%2C%20'output-box_3.png'%3A%20'output%20box_3'%2C%20'input_0.orig.png'%3A%20'uploaded%20image'%2C%20'output-vyv_3.png'%3A%20'output%20vyv_3'%2C%20'output-box_5.png'%3A%20'output%20box_5'%2C%20'output-am_5.png'%3A%20'output%20am_5'%2C%20'output-am_4.png'%3A%20'output%20am_4'%2C%20'input_0.sel.png'%3A%20'selected%20subimage'%2C%20'output-dct.png'%3A%20'output%20dct'%2C%20'output-deriche_4.png'%3A%20'output%20deriche_4'%2C%20'output-ebox_5.png'%3A%20'output%20ebox_5'%2C%20'output-sii_4.png'%3A%20'output%20sii_4'%2C%20'output-ebox_3.png'%3A%20'output%20ebox_3'%7D%2C%20'params'%3A%20%5B'sigma'%2C%20'fir'%2C%20'dct'%2C%20'box_3'%2C%20'box_4'%2C%20'box_5'%2C%20'ebox_3'%2C%20'ebox_4'%2C%20'ebox_5'%2C%20'sii_3'%2C%20'sii_4'%2C%20'sii_5'%2C%20'am_3'%2C%20'am_4'%2C%20'am_5'%2C%20'deriche_2'%2C%20'deriche_3'%2C%20'deriche_4'%2C%20'vyv_3'%2C%20'vyv_4'%2C%20'vyv_5'%5D%7D%2C%20'general'%3A%20%7B'demo_title'%3A%20'A%20Survey%20of%20Gaussian%20Convolution%20Algorithms'%2C%20'is_test'%3A%20'false'%2C%20'xlink_article'%3A%20'http%3A%2F%2Fwww.ipol.im%2Fpub%2Fart%2F2013%2F87%2F'%2C%20'param_description'%3A%20%5B''%5D%2C%20'input_description'%3A%20''%7D%7D%22"
demojson_decoded= "{'inputs': [{'description': 'input', 'max_pixels': '700 * 700', 'dtype': '3x8i', 'ext': '.png', 'type': 'image', 'max_weight': '10 * 1024 * 1024'}], 'results': [{'style': 'height:{{sizeY*ZoomFactor}}px', 'type': 'gallery', 'contents': {'Input': 'input_0.sel.png', 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=3': 'output-am_3.png', 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=5': 'output-am_5.png', 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=4': 'output-am_4.png', 'DCT': 'output-dct.png', 'FIR, <i>tol<\\\\/i>=10<sup>&minus;2<\\\\/sup>': 'output-fir.png', 'Exact*': 'output-exact.png', 'Box, <i>K<\\\\/i>=3': 'output-box_3.png', 'Box, <i>K<\\\\/i>=4': 'output-box_4.png', 'Box, <i>K<\\\\/i>=5': 'output-box_5.png', 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=5': 'output-vyv_5.png', 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=4': 'output-vyv_4.png', 'Extended box, <i>K<\\\\/i>=3': 'output-ebox_3.png', 'Extended box, <i>K<\\\\/i>=4': 'output-ebox_4.png', 'Extended box, <i>K<\\\\/i>=5': 'output-ebox_5.png', 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=3': 'output-vyv_3.png', 'SII, <i>K<\\\\/i>=3': 'output-sii_3.png', 'SII, <i>K<\\\\/i>=4': 'output-sii_4.png', 'SII, <i>K<\\\\/i>=5': 'output-sii_5.png', 'Deriche, <i>K<\\\\/i>=3': 'output-deriche_3.png', 'Deriche, <i>K<\\\\/i>=2': 'output-deriche_2.png', 'Deriche, <i>K<\\\\/i>=4': 'output-deriche_4.png'}, 'label': 'Images:'}, {'type': 'html_text', 'contents': [\"<p style='font-size:85%'>* &ldquo;Exact&rdquo; is computed with FIR, \", '<i>tol<\\\\/i>=10<sup>&minus;15<\\\\/sup>, for &sigma;&nbsp;&le;&nbsp;2 and ', 'DCT for &sigma;&nbsp;&gt;&nbsp;2 ', \"(using {{params.sigma<=2?'FIR':'DCT'}} for this experiment).<\\\\/p>\"]}, {'type': 'html_text', 'contents': ['<h2>Accuracy<\\\\/h2>', \"<table style='margin:0px;margin-top:10px;text-align:center'>\", '<tr>', '<th>Method<\\\\/th>', '<th>&nbsp;Max Diff&nbsp;<\\\\/th>', '<th>&nbsp;RMSE&nbsp;<\\\\/th>', '<th>&nbsp;PSNR&nbsp;<\\\\/th>', '<\\\\/tr>', '<tr ng-repeat=\\'(k,v) in info\\' ng-if=\\'k.indexOf(\"metrics_\")>-1\\'', 'ng-init=\\'alg={ \"fir\":\"FIR, <i>tol<\\\\/i>=10<sup>&minus;2<\\\\/sup>\", \"dct\":\"DCT\", \"box\":\"Box\", \"ebox\":\"Extended box\", \"sii\":\"SII\", \"deriche\":\"Deriche\" , \"vyv\":\"Vliet&ndash;Young&ndash;Verbeek\", \"am\":\"Alvarez&ndash;Mazorra\" }\\'>', '<td>', '<span ng-bind-html=\"alg[k.substr(8).split(\\'_\\')[0]]\"> <\\\\/span>', '<span ng-if=\"k.substr(8).split(\\'_\\').length>1\">', \", <i>K<\\\\/i>= {{k.substr(8).split('_')[1]}}\", '<\\\\/span>', '<\\\\/td>', \"<td> {{v.split('|')[0].split(':')[1]}} <\\\\/td>\", \"<td> {{v.split('|')[1].split(':')[1]}} <\\\\/td>\", \"<td> {{v.split('|')[2].split(':')[1]}} <\\\\/td>\", '<\\\\/tr>', '<\\\\/table>']}], 'params': [{'values': {'default': 5, 'max': 30, 'step': 0.01, 'min': 0.5}, 'type': 'range', 'id': 'sigma', 'label': '<i>&sigma;<\\\\/i>, Gaussian standard deviation'}, {'default': ['fir', 'dct'], 'values': [{'fir': 'FIR, <i>tol<\\\\/i>=10<sup>&minus;2<\\\\/sup>'}, {'dct': 'DCT'}, {'box_5': 'Box, <i>K<\\\\/i>=5', 'box_4': 'Box, <i>K<\\\\/i>=4', 'box_3': 'Box, <i>K<\\\\/i>=3'}, {'ebox_3': 'Extended box, <i>K<\\\\/i>=3', 'ebox_5': 'Extended box, <i>K<\\\\/i>=5', 'ebox_4': 'Extended box, <i>K<\\\\/i>=4'}, {'sii_3': 'SII, <i>K<\\\\/i>=3', 'sii_5': 'SII, <i>K<\\\\/i>=5', 'sii_4': 'SII, <i>K<\\\\/i>=4'}, {}, {'am_3': 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=3', 'am_5': 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=5', 'am_4': 'Alvarez&ndash;Mazorra, <i>K<\\\\/i>=4'}, {'deriche_4': 'Deriche, <i>K<\\\\/i>=4', 'deriche_2': 'Deriche, <i>K<\\\\/i>=2', 'deriche_3': 'Deriche, <i>K<\\\\/i>=3'}, {'vyv_3': 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=3', 'vyv_5': 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=5', 'vyv_4': 'Vliet&ndash;Young&ndash;Verbeek, <i>K<\\\\/i>=4'}], 'type': 'checkboxes', 'id': 'algo', 'label': 'Algorithms'}], 'build': [{'url': 'http://www.ipol.im/pub/art/2013/87/gaussian_20131215.tgz', 'srcdir': 'gaussian_20131215', 'binaries': [['.', 'gaussian_demo'], ['.', 'imdiff']], 'flags': '-j4  --makefile=makefile.gcc', 'build_type': 'make'}], 'run': ['run_algorithms.py'], 'config': {'info_from_file': {'metrics_box_3': 'metrics_box_3.txt', 'metrics_box_5': 'metrics_box_5.txt', 'metrics_box_4': 'metrics_box_4.txt', 'metrics_deriche_3': 'metrics_deriche_3.txt', 'metrics_dct': 'metrics_dct.txt', 'metrics_deriche_2': 'metrics_deriche_2.txt', 'metrics_fir': 'metrics_fir.txt', 'metrics_sii_4': 'metrics_sii_4.txt', 'metrics_sii_3': 'metrics_sii_3.txt', 'metrics_am_3': 'metrics_am_3.txt', 'metrics_vyv_3': 'metrics_vyv_3.txt', 'metrics_deriche_4': 'metrics_deriche_4.txt', 'metrics_vyv_5': 'metrics_vyv_5.txt', 'metrics_am_5': 'metrics_am_5.txt', 'metrics_vyv_4': 'metrics_vyv_4.txt', 'metrics_ebox_5': 'metrics_ebox_5.txt', 'metrics_ebox_4': 'metrics_ebox_4.txt', 'metrics_sii_5': 'metrics_sii_5.txt', 'metrics_ebox_3': 'metrics_ebox_3.txt', 'metrics_am_4': 'metrics_am_4.txt'}}, 'archive': {'files': {'output-deriche_2.png': 'output deriche_2', 'output-deriche_3.png': 'output deriche_3', 'output-sii_5.png': 'output sii_5', 'output-ebox_4.png': 'output ebox_4', 'output-am_3.png': 'output am_3', 'output-fir.png': 'output fir', 'output-box_4.png': 'output box_4', 'output-sii_3.png': 'output sii_3', 'output-vyv_5.png': 'output vyv_5', 'output-vyv_4.png': 'output vyv_4', 'output-box_3.png': 'output box_3', 'input_0.orig.png': 'uploaded image', 'output-vyv_3.png': 'output vyv_3', 'output-box_5.png': 'output box_5', 'output-am_5.png': 'output am_5', 'output-am_4.png': 'output am_4', 'input_0.sel.png': 'selected subimage', 'output-dct.png': 'output dct', 'output-deriche_4.png': 'output deriche_4', 'output-ebox_5.png': 'output ebox_5', 'output-sii_4.png': 'output sii_4', 'output-ebox_3.png': 'output ebox_3'}, 'params': ['sigma', 'fir', 'dct', 'box_3', 'box_4', 'box_5', 'ebox_3', 'ebox_4', 'ebox_5', 'sii_3', 'sii_4', 'sii_5', 'am_3', 'am_4', 'am_5', 'deriche_2', 'deriche_3', 'deriche_4', 'vyv_3', 'vyv_4', 'vyv_5']}, 'general': {'demo_title': 'A Survey of Gaussian Convolution Algorithms', 'is_test': 'false', 'xlink_article': 'http://www.ipol.im/pub/art/2013/87/', 'param_description': [''], 'input_description': ''}}"


class TestDemoinfo(unittest.TestCase):

	demoinfo = DemoInfo(CONFIGFILE)

	####################
	# individual tests #
	####################


	def add_demo_description_1(self):
		test_passed = True
		try:

			# CREATE demo_description
			#convert python dict to json (el dict, directamente, no es json valido, en jslint si,pq estoy pasando el dict a string al hacer copypaste)
			data_dict1 = json.dumps(json44)
			dd1=str(data_dict1)
			# print " is json",is_json(dd1)
			id1=self.demoinfo.add_demo_description_using_param(dd1)
			print " demodescription created: ",id1

			# CREATE demo_description
			data_dict2 = json.dumps(json81)
			dd2=str(data_dict2)
			# print " is json",is_json(dd2)
			id2=self.demoinfo.add_demo_description_using_param(dd2)
			print " demodescription created: ",id2

			# READ demo_description
			demojsonread = self.demoinfo.read_demo_description(1)

			# print "demojsonread ",demojsonread
			# print
			if not is_json(demojsonread):
				print ("demojsonread NOT JSON !!!!!")
				test_passed = False


		except Exception as ex:
			print "add_demo_description_1 ex: ",ex
			test_passed = False

		self.failUnless(test_passed, 'failure , add_demo_description_1 Failed ')


	def add_ddl_history_to_demo(self):
		test_passed = True
		try:

			#modify demo2 ddl history
			print " add_ddl_history_to_demo"
			demoid=2

			# READ all demodescriptions for demo
			demodescription_nojson_list=self.demoinfo.demo_get_demodescriptions_list(demoid)
			#demodescription_nojson_list=self.demoinfo.demo_get_demodescriptions_list(demoid,returnjsons=True)
			print
			print " demodescription_nojson_list",demodescription_nojson_list
			print " time: ",datetime.datetime.now()
			print

			#Add new ddl to demo, inproductio=True
			json1=str(json.dumps(json_g_roussos_diffusion_interpolation))
			dd=self.demoinfo.add_demo_description_using_param( json1)
			dd=json.loads(dd)
			ddid=int(dd['demo_description_id'])
			print " demo_description_id: ",ddid
			ddd=self.demoinfo.add_demodescription_to_demo(demoid,ddid)
			print " demo_dd: ",ddd
			print " demo description (in production = True by default)with id: %s added to demo %s"%(ddid,demoid)
			print

			#Add new ddl to demo, inproductio=False
			json2=str(json.dumps(json20))
			dd=self.demoinfo.add_demo_description_using_param(json2,inproduction=False)
			dd=json.loads(dd)
			ddid=int(dd['demo_description_id'])
			print " demo_description_id: ",ddid
			ddd=self.demoinfo.add_demodescription_to_demo(demoid,ddid)
			print " demo_dd: ",ddd
			print " demo description (in production = False ) with id: %s added to demo %s"%(ddid,demoid)
			print


			#Add new ddl to demo, inproductio=False
			json2=str(json.dumps(json81))
			dd=self.demoinfo.add_demo_description_using_param(json2,inproduction=True)
			dd=json.loads(dd)
			ddid=int(dd['demo_description_id'])
			print " demo_description_id: ",ddid
			ddd=self.demoinfo.add_demodescription_to_demo(demoid,ddid)
			print " demo_dd: ",ddd
			print " demo description (in production = False ) with id: %s added to demo %s"%(ddid,demoid)
			print

			# # CREATE demo_description
			# #convert python dict to json (el dict, directamente, no es json valido, en jslint si,pq estoy pasando el dict a string al hacer copypaste)
			# data_dict1 = json.dumps(json20)
			# dd1=str(data_dict1)
			# # print " is json",is_json(dd1)
			# id1=self.demoinfo.add_demo_description_using_param(dd1)
			# print " demodescription created: ",id1
			#
			# # CREATE demo_description
			# data_dict2 = json.dumps(json81)
			# dd2=str(data_dict2)
			# # print " is json",is_json(dd2)
			# id2=self.demoinfo.add_demo_description_using_param(dd2)
			# print " demodescription created: ",id2

			# # READ demo_description
			# demojsonread = self.demoinfo.read_demo_description(demoid)
			# print "demojsonread ",demojsonread
			# print
			# if not is_json(demojsonread):
			# 	print ("demojsonread NOT JSON !!!!!")
			# 	test_passed = False

			# READ all demodescriptions for demo
			demodescription_nojson_list=self.demoinfo.demo_get_demodescriptions_list(demoid,returnjsons=False)
			print
			print " demodescription_nojson_list",demodescription_nojson_list
			print " time: ",datetime.datetime.now()
			print

			# READ last demodescription for demo
			last_demodescription_nojson=self.demoinfo.read_last_demodescription_from_demo(demoid,returnjsons=False)
			print " last_demodescription_nojson",last_demodescription_nojson
			print " time: ",datetime.datetime.now()
			print

		except Exception as ex:
			print "add_ddl_history_to_demo ex: ",ex
			test_passed = False

		self.failUnless(test_passed, 'failure , add_ddl_history_to_demo Failed ')


	def special_test(self):
		test_passed = True
		try:

			#http://stackoverflow.com/questions/15900338/python-request-post-with-param-data

			# WS with JSON PARAMETER, not the best option, params are encoded
			print
			print (" This tests attacs DemoInfo module, so it DemoInfo must be running in localhost, its a more realistic test than the rest")
			print (" This tests attacs the real DB, not the test DB. Adds a demo description json to demo 1 into DB and reads it")
			print (" This also serves to help me init demo  whith data  so i can show it with CP app")
			print


			demojson = json81
			#demojson = {'demojson':{'var': 'data'}}


			# print (" add_demo_description_2 WS with JSON PARAMETER")
			# url = 'http://127.0.0.1:9002/add_demo_description_using_param'
			# print " demojson param is json",is_json(json.dumps(demojson))
			# #params y data son diferentes!!!los ws post deberian recibir data
			# params = {'demojson':json.dumps(demojson) }
			# r = requests.post(url, params=params)


			# ADD
			# WS with JSON AS DATA , no parms
			print (" add_demo_description_2 WS with JSON AS POST DATA")
			url = 'http://127.0.0.1:9002/add_demo_description'
			print " demojson data is json: ",is_json(json.dumps(demojson))
			#print " demojson ", demojson
			print " demojson: ...", str(demojson)[-150:]
			#r = requests.post(url, data=json.dumps(demojson))
			params = {'demoid':1 }
			r = requests.post(url, json=demojson,params=params)
			print
			print (" ADD DEMO WS with JSON AS POST DATA RESULT")
			print " url: ",r.url
			print " text: ",r.text
			print " headers: ",r.headers.get('content-type')
			print " result: ",r
			print

			#parse id from response
			import yaml
			print " parse id from response with YAM"
			resp_dict = yaml.safe_load(r.text) #dict, str not unicode
			print " resp_dict: ",resp_dict
			print " resp_dict type: ",type(resp_dict) #dict unicode
			print
			id=int(resp_dict["demo_description_id"])
			print " demojsonread id: ",id

			# READ
			# read_demo_description , must access not demo db,
			# yo u cannot use this now: demojsonread = self.demoinfo.read_demo_description(id)
			url = 'http://127.0.0.1:9002/read_demo_description'
			params = {'demodescriptionID':id }
			r = requests.post(url, params=params)

			print (" READ  RESULT")
			print " url: ",r.url
			print " text: ...",r.text[-50:]
			print " headers: ",r.headers.get('content-type')
			print " result: ",r
			print

			resp_dict = yaml.safe_load(r.text) # str
			#resp_dict = json.loads(r.text) # unicode
			print " resp_dict type: ",type(resp_dict)
			read_data = resp_dict["demo_description"]
			print " read_data type: ",type(read_data)
			print " read_data is_json: ",is_json(read_data)
			print "read_data: ..." ,read_data[-150:]
			print

			myjson = yaml.safe_load(read_data)
			print " json params original: " ,json81["params"]
			print
			print " json params: ",type(myjson["params"])
			print " json params: " ,myjson["params"]
			print

			#UPDATE
			# WS with JSON AS DATA , no parms
			print (" UPDATE  ---- update WS with JSON AS POST DATA")
			url = 'http://127.0.0.1:9002/update_demo_description'
			#demojson = {"demojson":{"key": "data"}}
			demojson = json44

			print " demojson data is json",is_json(json.dumps(demojson))
			# print " demojson ", demojson
			print " demojson ...", str(demojson)[-150:]
			print type(demojson)

			# #convert unicode str to dict for WS
			# demojson=json.loads(demojson)
			# print " demojson ...", str(demojson)[-150:]
			# print type(demojson)
			# #convert dict to  str
			demojson=json.dumps(demojson)
			print " demojson ...", str(demojson)[-150:]
			print type(demojson)
			params = {'demodescriptionID':id }
			r = requests.post(url, params=params, json=demojson )
			print (" add_demo_description_2 update WS with JSON AS POST DATA RESULT")
			# print " url: ",r.url
			# print " text: ",r.text
			# print " headers: ",r.headers.get('content-type')
			# print " result: ",r
			print


			#ADD DEMODESCRIPTION 1 TO  DEMO 1


			# READ
			url = 'http://127.0.0.1:9002/read_demo_description'
			params = {'demodescriptionID':id }
			r = requests.post(url, params=params)
			print
			print (" read_demo_description RESULT")
			print " url: ",r.url
			print " text: ...",r.text[-50:]
			print
			#resp_dict = yaml.safe_load(r.text) # str
			resp_dict=json.loads(r.text)

			read_data = resp_dict["demo_description"]
			print " read_data is_json: ",is_json(read_data)
			print " read status: ",resp_dict['status']
			print " read_data: ..." ,read_data[-150:]
			print


		except Exception as ex:
			print "special_test ",ex
			test_passed = False

		self.failUnless(test_passed, 'failure , edit_editor  updating  editor')


	def delete_db(self):
		# after running all tests clean db, its gets created and init when you instance DemoInfo
		dbname = DBNAME
		test_passed = True
		print " Delete tests DB"
		try:
			if os.path.isfile(dbname):
				try:
					os.remove(dbname)
				except Exception as ex:
					error_string=("DBremove e:%s"%(str(ex)))
					print (error_string)
			status = False
		except Exception as ex:
			error_string=("TEST delete_db  e:%s"%(str(ex)))
			print error_string
			test_passed = False

		self.failUnless(test_passed, 'failure , test_add_demo_1 Failed creating two demos')


	def add_demo_1(self):
		test_passed = True
		try:
			editorsdemoid = 23
			title = 'DemoTEST1 Title'
			abstract = 'DemoTEST1 Abstract'
			zipURL = 'https://DemoTEST1.html'
			active = 1
			stateID = 1
			demodescriptionID = 1

			demoid=self.demoinfo.add_demo(editorsdemoid,title, abstract, zipURL,active,stateID,demodescriptionID=demodescriptionID )
			print " created demo: ",demoid

			editorsdemoid = 24
			title = 'DemoTEST2 Title'
			abstract = 'DemoTEST2 Abstract'
			zipURL = 'https://DemoTEST2.html'
			active = 1
			stateID = 1

			#creates demo and creates it's demodescription (with id=3)
			demoid=self.demoinfo.add_demo(editorsdemoid,title, abstract, zipURL,active,stateID,demodescriptionJson = str(json_g_roussos_diffusion_interpolation))
			print " created demo: ",demoid
			print " time: ",datetime.datetime.now()


			editorsdemoid = 25
			title = 'DemoTEST3 Title'
			abstract = 'DemoTEST3 Abstract'
			zipURL = 'https://DemoTEST3.html'
			active = 1
			stateID = 1

			#creates demo and no demodescription
			demoid=self.demoinfo.add_demo(editorsdemoid,title, abstract, zipURL,active,stateID)
			print " created demo: ",demoid


		except Exception as ex:
			print "add_demo_1 ex: ", ex
			test_passed = False

		self.failUnless(test_passed, 'failure , test_add_demo_1 Failed creating two demos')


	def add_duplicated_demo(self):
		# create duplicated demo
		test_passed = False
		try:
			editorsdemoid = 26
			title = 'DemoTEST4 Title'
			abstract = 'DemoTEST4 Abstract'
			zipURL = 'https://DemoTEST4.html'
			active = 1
			stateID = 1
			demodescriptionID = 2
			self.demoinfo.add_demo(editorsdemoid,title, abstract, zipURL,active,stateID,demodescriptionID = demodescriptionID)

			editorsdemoid = 27
			title = 'DemoTEST4 Title'
			abstract = 'DemoTEST5 Abstract'
			zipURL = 'https://DemoTEST5.html'
			active = 1
			stateID = 1
			demodescriptionID = 2
			result = self.demoinfo.add_demo(editorsdemoid,title, abstract, zipURL,active,stateID,demodescriptionID = demodescriptionID)

			print result
			if 'error' in result:
				raise ValueError(result)


		except Exception as ex:
			print "add_duplicated_demo ex: ",ex
			test_passed = True

			# ajson = self.demoinfo.demo_list()
			# print ajson

		self.failUnless(test_passed, 'failure , add_duplicated_demo does not fail creating demo with the same tile')


	def add_author_1(self):
		test_passed = True
		try:
			name='Author Name1'
			mail = 'authoremail1@gmail.com'
			a1=self.demoinfo.add_author(name, mail)
			print " author created",a1

			name='Author Name2'
			mail = 'authoremail2@gmail.com'
			a2=self.demoinfo.add_author(name, mail)
			print " author created",


			name='Author Name3'
			mail = 'authoremail3@gmail.com'
			a3=self.demoinfo.add_author(name, mail)
			print " author created",a3


		except Exception as ex:
			test_passed = False

		self.failUnless(test_passed, 'failure , add_author_1 Failed creating two authors')


	def add_duplicated_author(self):

		test_passed = False
		try:
			name='Author Name3'
			mail = 'authoremail3@gmail.com'
			self.demoinfo.add_author(name, mail)

			name='Author Name3'
			mail = 'authoremail3@gmail.com'
			result=self.demoinfo.add_author(name, mail)

			print result
			if 'error' in result:
				raise ValueError(result)
		except Exception as ex:
			test_passed = True

		self.failUnless(test_passed, 'failure , add_duplicated_author does not fail creating two authors  with the same email ')


	def add_editor_1(self):
		test_passed = True
		try:
			name='editor Name1'
			mail = 'editoremail1@gmail.com'
			e1=self.demoinfo.add_editor(name, mail)
			print " editor created ",e1

			name='editor Name2'
			mail = 'editoremail2@gmail.com'
			e2=self.demoinfo.add_editor(name, mail)
			print " editor created ",e2

			name='editor Name3'
			mail = 'editoremail3@gmail.com'
			e3=self.demoinfo.add_editor(name, mail)
			print " editor created ",e3
		except Exception as ex:
			test_passed = False

		self.failUnless(test_passed, 'failure , add_editor_1 Failed creating two authors')


	def add_duplicated_editor(self):
		test_passed = False
		try:
			name='editor Name3'
			mail = 'editoremail3@gmail.com'
			self.demoinfo.add_editor(name, mail)

			name='editor Name3'
			mail = 'editoremail3@gmail.com'
			result=self.demoinfo.add_editor(name, mail)

			print result
			if 'error' in result:
				raise ValueError(result)


		except Exception as ex:
			test_passed = True

		self.failUnless(test_passed, 'failure , add_editor_2 does not fail creating two editors  with the same email ')


	def add_authors_and_editors_to_demo_1(self):
		test_passed = True
		try:

			self.demoinfo.add_author_to_demo(1 ,1)
			self.demoinfo.add_editor_to_demo(1 ,1)
			self.demoinfo.add_author_to_demo(1 ,3)
			self.demoinfo.add_editor_to_demo(1 ,3)
			self.demoinfo.add_author_to_demo(2 ,2)
			self.demoinfo.add_editor_to_demo(2 ,2)

		except Exception as ex:
			test_passed = False

		self.failUnless(test_passed, 'failure , add_editor_1 Failed adding editor/author to a demo  ')


	def add_duplicated_authors_to_demo(self):
		test_passed = False
		try:

			result=self.demoinfo.add_author_to_demo(1 ,1)
			print result
			if 'error' in result:
				raise ValueError(result)
		except Exception as ex:
			test_passed = True

		self.failUnless(test_passed, 'failure , add_authors_to_demo_2 does not fail creating two duplicate authors  with the same demo ')


	def add_duplicated_editors_to_demo(self):
		test_passed = False
		try:

			result=self.demoinfo.add_editor_to_demo(1 ,1)
			print result
			if 'error' in result:
				raise ValueError(result)
		except Exception as ex:
			test_passed = True

		self.failUnless(test_passed, 'failure , add_editors_to_demo_3 does not fail creating two duplicate editors  with the same demo ')


	def remove_authors_and_editors_to_demo_1(self):
		test_passed = True
		try:

			self.demoinfo.remove_author_from_demo(1 ,3)
			self.demoinfo.remove_editor_from_demo(1 ,3)

			ajson = self.demoinfo.demo_get_authors_list(1)
			# print ajson
			if not "\"id\": 1" in ajson or "\"id\": 3" in ajson:
				print "only author 1 not found in demo 1"
				raise Exception

			ejson = self.demoinfo.demo_get_editors_list(1)
			#print ejson
			if not "\"id\": 1" in ejson or "\"id\": 3" in ejson:
				print "only editor 1 not found in demo 1"
				raise Exception

		except Exception as ex:
			test_passed = False

		self.failUnless(test_passed, 'failure , remove_authors_and_editors_to_demo_1 Failed removing editor/author to a demo  ')


	def edit_demo(self):
		test_passed = True
		try:



			ajson = self.demoinfo.demo_list()
			print ' demo list before update demo', ajson
			print


			json_demo_1='{"modification": "2015-12-02 13:24:43", "title": "newdemo1", "abstract": "newdemo1abstract","creation": "2015-12-02 13:24:43", "editorsdemoid": 1, "active": 1, "stateID": 1, "id": 1, "zipURL": "http://demo1updated.com"}'
			self.demoinfo.update_demo(json_demo_1)

			ajson = self.demoinfo.demo_list()
			print ' demo list after update demo', ajson

			if not "newdemo1" in ajson or not "newdemo1abstract" in ajson or not "http://demo1updated.com" in ajson:
				print "Demo update failed"
				raise Exception



		except Exception as ex:
			print "edit_demo: ",ex
			test_passed = False

		self.failUnless(test_passed, 'failure , edit demo')


	def edit_author(self):

		test_passed = True
		try:

			al = self.demoinfo.demo_get_authors_list(1)
			print " author list before: ",al
			print


			json_author_1='{"mail": "authoremail1_updated@gmail.com", "creation": "2015-12-03 20:53:07", "id": 1, "name": "Author_Name1_updated"}'
			self.demoinfo.update_author(json_author_1)
			al = self.demoinfo.demo_get_authors_list(1)
			print " author list after: ",al

			if not "authoremail1_updated" in al or not "Author_Name1_updated" in al:
				print "Author update failed"
				raise Exception

		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , edit_author  updating  authors')


	def edit_editor(self):
		test_passed = True
		try:

			ejson = self.demoinfo.demo_get_authors_list(1)
			print " editor list before: ",ejson
			print

			json_editor_1='{"mail": "editoremail1_updated@gmail.com", "creation": "2015-12-03 20:53:07","active": 1, "id": 1, "name": "Editor_Name1_updated"}'
			self.demoinfo.update_editor(json_editor_1)
			el = self.demoinfo.demo_get_editors_list(1)
			print " editor list after: ",el

			if not "editoremail1_updated" in el or not "Editor_Name1_updated" in el:
				print "Editor update failed"
				raise Exception



		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , edit_editor  updating  editor')


	def read_demo(self):
		test_passed = True
		try:


			demo1 = self.demoinfo.read_demo(1)
			print "read demo1: ",demo1.__dict__

			demo2 = self.demoinfo.read_demo(2)
			print "read demo2: ",demo2.__dict__

			demo2json = self.demoinfo.read_demo_metainfo(2)
			print "read demo2 demo2json: ",demo2json





		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , reading  demos before deleting them ')


	def remove_demo(self):
		test_passed = True
		try:

			#initial
			dl0 = self.demoinfo.demo_list()

			#no hard_delete demo 1
			print " no hard_delete demo 1"
			self.demoinfo.delete_demo(1)
			dl1 = self.demoinfo.demo_list()
			al_demo1= self.demoinfo.demo_get_authors_list(1)
			if  ('"id": 1' in dl0) and ('"id": 1' in dl1) and (not "\"id\": 1" in al_demo1) :
				print "Demo 1 delete failed"
				raise Exception

			# hard_delete demo 2
			print " hard_delete demo 2"
			al_demo2_init = self.demoinfo.demo_get_authors_list(2)
			self.demoinfo.delete_demo(2,hard_delete = True)
			dl2 = self.demoinfo.demo_list()
			al_demo2 = self.demoinfo.demo_get_authors_list(2)
			if ('"id": 2' in dl0) and ('"id": 2' in dl2) and ("\"id\": 2" in al_demo2_init) and ("\"id\": 2" in al_demo2):
				print "Demo 2 hard delete failed"
				raise Exception


			# print
			# print " Initial Demo list"
			# print dl0
			# print
			# print " Demo list after delete demo 1 no hard delete"
			# print dl1
			# print
			# print "al_demo1"
			# print al_demo1
			# print
			# print " Initial Author list for demo 2"
			# print al_demo2_init
			# print
			# print "  Demo list after hard delete demo 2"
			# print dl2
			# print
			# print "al_demo2"
			# print al_demo2

		except Exception as ex:
			print "remove demos",ex
			test_passed = False

		self.failUnless(test_passed, 'failure , removing demos ')


	def read_by_editordemoid(self):
		test_passed = True
		try:



			add_demo_1__editordemoid = 13333
			demojson = self.demoinfo.read_demo_metainfo_by_editordemoid(add_demo_1__editordemoid)
			print "read demo1 retrieved by editordemoid: %d demojson: %s "%(add_demo_1__editordemoid,demojson)


			add_demo_1__editordemoid = 1
			demojson = self.demoinfo.read_demo_metainfo_by_editordemoid(add_demo_1__editordemoid)
			print "read demo1 retrieved by editordemoid: %d demojson: %s "%(add_demo_1__editordemoid,demojson)


		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , reading  demos before deleting them ')


	def list_demos_pagination_filter(self):
		test_passed = True
		try:


			ajson = self.demoinfo.demo_list()
			print ' demo list ', ajson
			print

			num_elements_page = 2
			page = 1
			qfilter = 'ddd'
			ajson = self.demoinfo.demo_list_pagination_and_filter(num_elements_page,page,qfilter)
			print
			print " num_elements_page: ", num_elements_page
			print " page: ", page
			print " qfilter: ", qfilter
			print
			print ' demo list filtered and pagination, no result', ajson

			num_elements_page = 2
			page = 1
			qfilter = 'DemoTEST3'
			ajson = self.demoinfo.demo_list_pagination_and_filter(num_elements_page,page,qfilter)
			print
			print " num_elements_page: ", num_elements_page
			print " page: ", page
			print " qfilter: ", qfilter
			print
			print ' demo list filtered and pagination', ajson



			num_elements_page = 1
			page = 1
			qfilter = 'Demo'
			ajson = self.demoinfo.demo_list_pagination_and_filter(num_elements_page,page,qfilter)
			print
			print " num_elements_page: ", num_elements_page
			print " page: ", page
			print " qfilter: ", qfilter
			print
			print ' demo list filtered and pagination', ajson


			num_elements_page = 1
			page = 2
			qfilter = 'Demo'
			ajson = self.demoinfo.demo_list_pagination_and_filter(num_elements_page,page,qfilter)
			print
			print " num_elements_page: ", num_elements_page
			print " page: ", page
			print " qfilter: ", qfilter
			print
			print ' demo list filtered and pagination', ajson

		except Exception as ex:
			print "edit_demo: ",ex
			test_passed = False

		self.failUnless(test_passed, 'failure , edit demo')


	def read_states(self):
		test_passed = True
		try:

			stateslist = self.demoinfo.read_states()
			print "stateslist json: ",stateslist


		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , reading states ')


	def read_delete_author(self):
		test_passed = True
		try:

			#
			# name='Author Name3'
			# mail = 'authoremail3@gmail.com'
			# a3=self.demoinfo.add_author(name, mail)
			# print " author created",a3
			#



			demoid = 1
			authorid = 3

			a3 = self.demoinfo.read_author(authorid)
			print " author: %d : "%(authorid)
			print a3
			print

			self.demoinfo.add_author_to_demo(demoid ,authorid)
			print " author: %d added to demo: %d "%(authorid,demoid)
			print

			dl = self.demoinfo.demo_get_authors_list(demoid)
			print " author list for demo: %d "%(demoid)
			print
			print dl

			self.demoinfo.remove_author(authorid)
			print
			print " author: %d removed from demo: %d "%(authorid,demoid)
			print

			dl = self.demoinfo.demo_get_authors_list(demoid)
			print " author list for demo: %d "%(demoid)
			print
			print dl
			print

			al = self.demoinfo.author_list()
			print " complete author list:  "
			print
			print al
			print

			self.demoinfo.add_author_to_demo(demoid ,authorid)
			print " author: %d added to demo: %d "%(authorid,demoid)
			print

			dl = self.demoinfo.demo_get_authors_list(demoid)
			print " error if try to add inexistent author to demo"

			print " author list for demo: %d "%(demoid)
			print
			print dl

		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , delete_author_3 Failed ')


	def read_delete_editor(self):
		test_passed = True
		try:

			# name='editor Name3'
			# mail = 'editoremail3@gmail.com'
			# e3=self.demoinfo.add_editor(name, mail)
			# print " editor created ",e3

			demoid = 1
			editorid = 3

			e3 = self.demoinfo.read_editor(editorid)
			print " editor: %d : "%(editorid)
			print e3
			print

			self.demoinfo.add_editor_to_demo(demoid ,editorid)
			print " editor: %d added to demo: %d "%(editorid,demoid)
			print

			dl = self.demoinfo.demo_get_editors_list(demoid)
			print " editor list for demo: %d "%(demoid)
			print
			print dl

			self.demoinfo.remove_editor(editorid)
			print
			print " editor: %d removed from demo: %d "%(editorid,demoid)
			print

			dl = self.demoinfo.demo_get_editors_list(demoid)
			print " editor list for demo: %d "%(demoid)
			print
			print dl
			print

			el = self.demoinfo.editor_list()
			print " complete editor list:  "
			print
			print el

		except Exception as ex:
			print ex
			test_passed = False

		self.failUnless(test_passed, 'failure , delete_author_3 Failed ')


	##########################
	# run all tests in order #
	##########################

	def test_steps(self):
		#run in order all tests
		try:

			print
			print(" Monolithic Test Started")
			print(" From the initialized Db, with no demos,authors o editors, create them and manipulate them using the WS provided by demoInfo module")


			print " ---0"
			print
			self.add_demo_description_1()
			print
			print " ---1"
			print
			self.add_demo_1()
			print
			print " ---2"
			print
			self.add_duplicated_demo()
			print
			print " ---3"
			print
			self.add_author_1()
			print
			print " ---4"
			print
			self.add_duplicated_author()
			print
			print " ---5"
			print
			self.add_editor_1()
			print
			print " ---6"
			print
			self.add_duplicated_editor()
			print
			print " ---7"
			print
			self.add_authors_and_editors_to_demo_1()
			print
			print " ---8"
			print
			self.add_duplicated_authors_to_demo()
			print
			print " ---9"
			print
			self.add_duplicated_editors_to_demo()
			print
			print " ---10"
			print
			self.remove_authors_and_editors_to_demo_1()
			print
			print " ---11"
			print
			self.edit_demo()
			print
			print " ---12"
			print
			self.edit_author()
			print
			print " ---13"
			print
			self.edit_editor()
			print
			print " ---14"
			print
			self.read_demo()
			print
			print " ---15"
			print
			self.add_ddl_history_to_demo()
			print
			print " ---16"
			print
			self.remove_demo()
			print
			print " ---17"
			print
			self.read_states()
			print
			print " ---18"
			print
			self.read_by_editordemoid()
			print " ---19"
			print
			self.list_demos_pagination_filter()
			print
			print " ---20"
			print
			self.read_delete_author()
			print
			print " ---21"
			print
			self.read_delete_editor()
			print
			print
			print " ---22 SPECIAL TEST, DEMOINFO MODULE MUST BE RUNNING"
			#app demoinfo must be running ! works with the NOT TEST database
			# for testing ws that get the json from the the data, not params
			self.special_test()
			print
			print " ---cleanup"
			self.delete_db()
			print(" Monolithic Test Ended")

		except Exception as ex:
			print " ---cleanup"
			self.delete_db()
			raise ex


def main():
	unittest.main()


if __name__ == '__main__':
	main()