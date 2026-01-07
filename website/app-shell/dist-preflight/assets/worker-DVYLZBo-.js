import{f as o,z as s}from"./index-BnpC133k.js";/**
 * @license lucide-react v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l=o("History",[["path",{d:"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8",key:"1357e3"}],["path",{d:"M3 3v5h5",key:"1xhq8a"}],["path",{d:"M12 7v5l4 2",key:"1fdv2h"}]]);/**
 * @license lucide-react v0.294.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p=o("Sparkles",[["path",{d:"m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z",key:"17u4zn"}],["path",{d:"M5 3v4",key:"bklmnn"}],["path",{d:"M19 17v4",key:"iiml17"}],["path",{d:"M3 5h4",key:"nem4j1"}],["path",{d:"M17 19h4",key:"lbex7p"}]]);async function u(a,e){const{data:r}=await s.post(`/api/v1/workers/${a}/run`,e);return r}async function d(a,e){var r,t;try{const{data:n}=await s.post(`/api/v1/workers/${a}/validate-brand`,e);return n}catch(n){return{valid:!1,errors:((t=(r=n.response)==null?void 0:r.data)==null?void 0:t.errors)||["Validation failed"]}}}async function y(a,e){try{const r=a?`/api/v1/workers/${a}/runs`:"/api/v1/workers/business-builder/runs",{data:t}=await s.get(r,{params:e});return Array.isArray(t)?t:(t==null?void 0:t.items)||[]}catch{return[]}}async function h(a,e){const{data:r}=await s.post(`/api/v1/workers/${a}/replay`,{run_id:e});return r}async function k(){try{const{data:a}=await s.get("/api/v1/workers/health");return a}catch{return{status:"unhealthy",workers_available:0,last_check:new Date().toISOString()}}}export{l as H,p as S,k as g,y as l,h as r,u as s,d as v};
