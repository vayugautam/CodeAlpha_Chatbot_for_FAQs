const API=(import.meta.env.VITE_API_BASE_URL||'').replace(/\/$/,'');
const TOKEN='codealpha_faq_access_token';
export class ApiError extends Error { constructor(message,status=0){super(message);this.status=status;} }
async function request(path,options={}){
 const token=sessionStorage.getItem(TOKEN);const headers=new Headers(options.headers||{});
 if(token)headers.set('Authorization',`Bearer ${token}`);
 if(options.body)headers.set('Content-Type','application/json');
 const response=await fetch(`${API}${path}`,{...options,headers});
 const body=response.status===204?null:await response.json().catch(()=>null);
 if(response.status===401){sessionStorage.removeItem(TOKEN);window.dispatchEvent(new Event('codealpha:unauthorized'));}
 if(!response.ok)throw new ApiError(body?.detail||`Request failed (${response.status})`,response.status);
 return body;
}
export const api={
 register:(email,password)=>request('/auth/register',{method:'POST',body:JSON.stringify({email,password})}),
 login:(email,password)=>request('/auth/login',{method:'POST',body:JSON.stringify({email,password})}), me:()=>request('/auth/me'),
 conversations:()=>request('/conversations'), conversation:(id)=>request(`/conversations/${id}`),
 createConversation:(title='New conversation')=>request('/conversations',{method:'POST',body:JSON.stringify({title})}),
 deleteConversation:(id)=>request(`/conversations/${id}`,{method:'DELETE'}),
 chat:(id,message)=>request(`/conversations/${id}/chat`,{method:'POST',body:JSON.stringify({message})})
};
export {TOKEN};
