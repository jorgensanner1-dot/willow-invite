#!/bin/bash
# usage: tools_crop.sh PDF OUTPREFIX x0 y0 x1 y1 [dpi]   (page inches from bottom-left of sheet)
PDF=$1; OUT=$2; X0=$3; Y0=$4; X1=$5; Y1=$6; R=${7:-50}
PX=$(python3 -c "print(int($X0*$R))"); PY=$(python3 -c "print(int((42.25-$Y1)*$R))")
W=$(python3 -c "print(int(($X1-$X0)*$R))"); H=$(python3 -c "print(int(($Y1-$Y0)*$R))")
pdftoppm -r $R -x $PX -y $PY -W $W -H $H -png -singlefile "$PDF" "$OUT"
