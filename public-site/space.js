// Three.js 0.185.x, existing project dependency, MIT. Original scene implementation.
// This scene models a DOCUMENT RELATIONSHIP, not product internals.
import * as THREE from 'three';
export async function mountSpace(launch){
 const host=launch.querySelector('.space-host'),controls=launch.querySelector('.space-controls');
 const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setClearColor(0x0d110b,1);host.append(renderer.domElement);host.classList.add('ready');controls.hidden=false;
 const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(40,1,.1,100);camera.position.set(0,.5,9);camera.lookAt(0,0,0);const group=new THREE.Group();scene.add(group);group.rotation.set(-.08,-.3,0);
 const textures=[],meshes=[],geometries=[],materials=[];
 function makePanel(title,sub,index,color){const c=document.createElement('canvas');c.width=800;c.height=480;const ctx=c.getContext('2d');ctx.fillStyle='#1b2518';ctx.fillRect(0,0,800,480);ctx.strokeStyle=color;ctx.lineWidth=3;ctx.strokeRect(18,18,764,444);ctx.fillStyle=color;ctx.font='22px monospace';ctx.fillText(`0${index+1} / PROJECT EVIDENCE`,50,80);ctx.fillStyle='#f1ecdf';ctx.font='52px sans-serif';ctx.fillText(title,50,175);ctx.fillStyle='#a4af99';ctx.font='25px sans-serif';ctx.fillText(sub,50,237);ctx.strokeStyle='#a4af9933';for(let i=0;i<4;i++){ctx.beginPath();ctx.moveTo(50,300+i*24);ctx.lineTo(560-i*40,300+i*24);ctx.stroke()}ctx.fillStyle='#d0b27f';ctx.font='20px sans-serif';ctx.fillText('资料分层 · 非内部工程模型',50,420);const texture=new THREE.CanvasTexture(c);texture.colorSpace=THREE.SRGBColorSpace;textures.push(texture);const geometry=new THREE.BoxGeometry(3.7,2.25,.045);geometries.push(geometry);const face=new THREE.MeshBasicMaterial({map:texture}),edge=new THREE.MeshBasicMaterial({color:0x5b644a});materials.push(face,edge);const mesh=new THREE.Mesh(geometry,[edge,edge,edge,edge,face,face]);mesh.position.set((index-1)*.55,(index-1)*.22,(index-1)*.62);group.add(mesh);meshes.push(mesh)}
 makePanel('硬件资料','选品 / 产品定义 / 供应商评估',0,'#cda37d');makePanel('App 规划','需求 / 功能定义 / 版本待核',1,'#a8bd92');makePanel('AI 试点','场景 / 供应商 / 小样本验证',2,'#8da8b3');
 const grid=new THREE.GridHelper(18,24,0x4c583c,0x202a1c);grid.position.y=-2;scene.add(grid);geometries.push(grid.geometry);materials.push(grid.material);
 let disposed=false,angle=-.3,explode=0,pointer=null,raf=0;
 function render(){if(disposed)return;renderer.render(scene,camera)}
 function resize(){renderer.setSize(host.clientWidth,host.clientHeight,false);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();render()}
 const ro=new ResizeObserver(resize);ro.observe(host);resize();
 function place(){group.rotation.y=angle;meshes.forEach((m,i)=>{m.position.x=(i-1)*(.55+explode*1.65);m.position.y=(i-1)*(.22+explode*.18);m.position.z=(i-1)*(.62+explode*.15);m.rotation.y=(i-1)*explode*.13});render()}
 const handlers=[];function on(el,type,fn,options){el.addEventListener(type,fn,options);handlers.push(()=>el.removeEventListener(type,fn,options))}
 launch.querySelectorAll('[data-space-turn]').forEach(b=>on(b,'click',()=>{angle+=Number(b.dataset.spaceTurn)*.2;place()}));on(launch.querySelector('[data-space-explode]'),'click',()=>{explode=1-explode;place()});
 on(host,'keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft'||e.key==='ArrowRight')angle+=(e.key==='ArrowRight'?1:-1)*.18;else explode=e.key==='ArrowUp'?1:0;place()});
 on(renderer.domElement,'pointerdown',e=>{pointer={x:e.clientX,angle};renderer.domElement.setPointerCapture(e.pointerId)});on(renderer.domElement,'pointermove',e=>{if(pointer){angle=pointer.angle+(e.clientX-pointer.x)*.006;place()}});on(renderer.domElement,'pointerup',()=>{pointer=null});on(renderer.domElement,'pointercancel',()=>{pointer=null});place();
 return ()=>{disposed=true;cancelAnimationFrame(raf);ro.disconnect();handlers.forEach(fn=>fn());textures.forEach(t=>t.dispose());geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());renderer.dispose();renderer.domElement.remove();host.classList.remove('ready')};
}
