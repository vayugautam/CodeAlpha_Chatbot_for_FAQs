import {Navigate,Outlet} from 'react-router';import {useAuth} from '../context/AuthContext';
export default function Protected(){const {user,loading}=useAuth();if(loading)return <div className="center">Loading your account…</div>;return user?<Outlet/>:<Navigate to="/auth" replace/>;}
