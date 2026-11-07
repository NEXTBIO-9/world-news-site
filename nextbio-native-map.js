/* NEXT BIO v50: Natural Earth 10m equirectangular SVG and news pins share one geographic projection. */
(function(){'use strict';
const R=Math.PI/180,MAX=89.9;
const clamp=(n,a,b)=>Math.min(b,Math.max(a,n));
const latY=lat=>(90-clamp(lat,-90,90))/180;
const lonX=lon=>(lon+180)/360;
function create(id){
 const root=document.getElementById(id);if(!root)throw Error('Map container missing');
 root.replaceChildren();root.classList.add('nb-native-map');
 const style=document.createElement('style');style.textContent=`
 #map.nb-native-map{position:relative;overflow:hidden;touch-action:none;user-select:none;background:#eef2f5}
 #map.nb-native-map.nb-map-dark{background:#091827}
 #map .nb-native-world{position:absolute;left:0;top:0;pointer-events:none;will-change:transform}
 #map .nb-native-world img{position:absolute;left:0;top:0;width:100%;height:100%;max-width:none;object-fit:contain;pointer-events:none;display:block}
 #map .nb-native-world img.nb-dark{opacity:0}
 #map.nb-map-dark .nb-native-world img.nb-light{opacity:0}
 #map.nb-map-dark .nb-native-world img.nb-dark{opacity:1}
 #map .nb-native-markers{position:absolute;inset:0;pointer-events:none;z-index:3}
 #map .nb-native-marker{position:absolute;transform:translate(-50%,-50%);border:0;background:transparent;padding:0;cursor:pointer;pointer-events:auto;z-index:2}
 #map .nb-native-marker .news-pin{display:flex;align-items:center;justify-content:center;width:30px;height:30px}
 #map .nb-native-controls{position:absolute;left:12px;top:12px;z-index:5;display:grid;border:1px solid #aab5c3;border-radius:5px;overflow:hidden;box-shadow:0 1px 5px #0003}
 #map .nb-native-controls button{width:31px;height:31px;border:0;background:#fff;color:#1b334d;font-size:22px;cursor:pointer}
 #map .nb-native-controls button+button{border-top:1px solid #cdd5df}
 #map.nb-map-dark .nb-native-controls button{background:#22354c;color:#f1f5f9}
 `;document.head.appendChild(style);
 const world=document.createElement('div');world.className='nb-native-world';root.appendChild(world);
 const markers=document.createElement('div');markers.className='nb-native-markers';root.appendChild(markers);
 const controls=document.createElement('div');controls.className='nb-native-controls';
 for(const [symbol,delta,label] of [['+',1,'확대'],['−',-1,'축소']]){const b=document.createElement('button');b.type='button';b.textContent=symbol;b.title=label;b.setAttribute('aria-label',label);b.onclick=()=>zoomTo(zoom+delta,root.clientWidth/2,root.clientHeight/2);controls.appendChild(b);}root.appendChild(controls);
 const copies=[];for(let i=-2;i<=2;i++){const el=document.createElement('div');el.style.position='absolute';el.style.top='0';el.style.left='0';el.style.width='100%';el.style.height='100%';for(const [name,cls] of [['light','nb-light'],['dark','nb-dark']]){const img=document.createElement('img');img.className=cls;img.src=`./nextbio-world-map-${name}.svg`;img.alt='';img.draggable=false;el.appendChild(img);}world.appendChild(el);copies.push({el,i});}
 let zoom=2,center=[0,0],items=[],drag=null,handlers={},flight=null;
 const cancelFlight=()=>{if(flight!==null){cancelAnimationFrame(flight);flight=null;}};
 const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
 const mercLat=y=>90-180*y;
 function size(){return Math.max(512*Math.pow(2,zoom-1),root.clientWidth,root.clientHeight*2)}
 function centerXY(){return [lonX(center[1])*size(),latY(center[0])*size()/2]}
 function xy(lat,lon){const [cx,cy]=centerXY(),s=size();return [root.clientWidth/2+(lonX(lon)*s-cx),root.clientHeight/2+(latY(lat)*s/2-cy)]}
 function repaint(){const s=size(),[cx,cy]=centerXY();world.style.width=s+'px';world.style.height=(s/2)+'px';world.style.left=(root.clientWidth/2-cx)+'px';world.style.top=(root.clientHeight/2-cy)+'px';for(const c of copies)c.el.style.transform=`translateX(${c.i*100}%)`;
  for(const item of items){let [x,y]=xy(item.lat,item.lon);/* Choose the closest repeated world copy, without shifting the geographic point. */x+=Math.round((root.clientWidth/2-x)/s)*s;item.el.style.left=x+'px';item.el.style.top=y+'px';item.el.style.display=(y< -20||y>root.clientHeight+20||x< -20||x>root.clientWidth+20)?'none':'';}}
 function setView(latlon,z){cancelFlight();center=[clamp(+latlon[0],-MAX,MAX),+latlon[1]];zoom=clamp(+z,2,7);repaint();return api;}
 function zoomTo(z,px,py){cancelFlight();const old=size(),wx=lonX(center[1])+(px-root.clientWidth/2)/old,wy=latY(center[0])+(py-root.clientHeight/2)/(old/2);zoom=clamp(z,2,7);const ns=size(),nx=wx-(px-root.clientWidth/2)/ns,ny=wy-(py-root.clientHeight/2)/(ns/2);center=[mercLat(ny),nx*360-180];center[0]=clamp(center[0],-MAX,MAX);repaint();}
 root.addEventListener('wheel',e=>{e.preventDefault();zoomTo(zoom+(e.deltaY<0?.5:-.5),e.offsetX,e.offsetY);},{passive:false});
 root.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;cancelFlight();drag={x:e.clientX,y:e.clientY,lat:center[0],lon:center[1]};root.setPointerCapture(e.pointerId);});
 root.addEventListener('pointermove',e=>{if(!drag)return;const s=size(),dx=e.clientX-drag.x,dy=e.clientY-drag.y;const ny=latY(drag.lat)-dy/(s/2);center=[clamp(mercLat(ny),-MAX,MAX),drag.lon-dx/s*360];repaint();if(Math.abs(dx)+Math.abs(dy)>5&&handlers.dragstart&&!drag.fired){drag.fired=true;handlers.dragstart.forEach(fn=>fn());}});
 root.addEventListener('pointerup',()=>{drag=null;});root.addEventListener('pointercancel',()=>{drag=null;});
 function flyTo(loc,z,options={}){
  cancelFlight();
  const start=performance.now(),duration=Math.max(0.15,Math.min(6,Number(options.duration)||1.8))*1000;
  const fromLat=latY(center[0]),toLat=latY(+loc[0]);
  const fromLon=center[1];
  // Use the shortest east/west path, including across the date line.
  const lonDelta=((+loc[1]-fromLon+540)%360+360)%360-180;
  const fromZoom=zoom,toZoom=clamp(Number(z)||zoom,2,7);
  function tick(now){
   const t=clamp((now-start)/duration,0,1),p=ease(t);
   center=[clamp(mercLat(fromLat+(toLat-fromLat)*p),-MAX,MAX),fromLon+lonDelta*p];
   zoom=fromZoom+(toZoom-fromZoom)*p;
   repaint();
   if(t<1)flight=requestAnimationFrame(tick);else flight=null;
  }
  flight=requestAnimationFrame(tick);return api;
 }
 const api={setView,flyTo,getZoom:()=>zoom,getContainer:()=>root,invalidateSize:()=>{repaint();return api;},setTheme:dark=>root.classList.toggle('nb-map-dark',dark),on:(event,fn)=>{(handlers[event]??=[]).push(fn);return api;},createMarkerLayer:()=>({clearLayers(){items=[];markers.replaceChildren();},addMarker(loc,count,name,selected){const el=document.createElement('button');el.type='button';el.className='nb-native-marker';el.title=`${name} · ${count}건`;el.setAttribute('aria-label',el.title);const pin=document.createElement('span');pin.className='news-pin'+(selected?' selected':'');pin.textContent=count;el.appendChild(pin);markers.appendChild(el);const item={el,lat:loc[0],lon:loc[1]};items.push(item);el.addEventListener('pointerdown',e=>e.stopPropagation());repaint();return {on(event,fn){if(event==='click')el.addEventListener('click',fn);return this;}};}})};
 if(typeof ResizeObserver!=='undefined'){const ro=new ResizeObserver(()=>repaint());ro.observe(root);}
 setView([0,0],2);return api;
}
window.NEXTBIO_NATIVE_MAP={create};
})();
