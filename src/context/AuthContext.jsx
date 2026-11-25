import {createContext,useContext,useEffect,useMemo,useState} from 'react';
import {api,TOKEN} from '../api/client';
const Context=createContext(null);
export function AuthProvider({children}){
 const [user,setUser]=useState(null),[loading,setLoading]=useState(true);
 useEffect(()=>{if(!sessionStorage.getItem(TOKEN)){setLoading(false);return;}api.me().then(setUser).catch(()=>sessionStorage.removeItem(TOKEN)).finally(()=>setLoading(false));},[]);
 useEffect(()=>{const expire=()=>setUser(null);window.addEventListener('codealpha:unauthorized',expire);return()=>window.removeEventListener('codealpha:unauthorized',expire);},[]);
 const login=async(email,password)=>{const r=await api.login(email,password);sessionStorage.setItem(TOKEN,r.access_token);setUser(await api.me());};
 const register=async(email,password)=>{await api.register(email,password);await login(email,password);};
 const logout=()=>{sessionStorage.removeItem(TOKEN);setUser(null);};
 const value=useMemo(()=>({user,loading,login,register,logout}),[user,loading]);
 return <Context.Provider value={value}>{children}</Context.Provider>;
}
export const useAuth=()=>useContext(Context);
