// Export existing editable vector masks; original product pixels are preserved.
const fs=require('fs'),path=require('path');
const {Resvg}=require(process.env.NELSON_RESVG_MODULE||'@resvg/resvg-js');
const root=path.resolve(__dirname,'..');const results=[];
for(const name of ['001-cutout','device-cylinder','device-curved','yikou-blue','yikou-green','yikou-red']){
 const svg=fs.readFileSync(path.join(root,'assets',name+'.svg'));
 const output=new Resvg(svg,{font:{loadSystemFonts:false}}).render();const pixels=output.pixels;
 let opaque=0,minX=output.width,minY=output.height,maxX=0,maxY=0;
 for(let y=0;y<output.height;y++)for(let x=0;x<output.width;x++){if(pixels[(y*output.width+x)*4+3]>16){opaque++;minX=Math.min(x,minX);minY=Math.min(y,minY);maxX=Math.max(x,maxX);maxY=Math.max(y,maxY)}}
 if(!opaque)throw new Error(name+' rendered blank');
 fs.writeFileSync(path.join(root,'assets',name+'.png'),output.asPng());
 results.push({name,width:output.width,height:output.height,opaquePixels:opaque,alphaBounds:{minX,minY,maxX,maxY},bytes:output.asPng().length});
}
fs.writeFileSync(path.join(root,'qa','cutout-pixel-audit.json'),JSON.stringify(results,null,2));console.log(results);
