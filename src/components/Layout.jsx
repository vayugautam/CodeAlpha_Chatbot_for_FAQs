import {Link,Outlet,useNavigate} from 'react-router';
import {useAuth} from '../context/AuthContext';
export default function Layout(){const {user,logout}=useAuth();const go=useNavigate();return <div className="shell"><header><Link className="brand" to="/">☁ Cloudify <span>FAQ assistant</span></Link><nav>{user?<><Link to="/dashboard">Dashboard</Link><Link to="/conversations">History</Link><button className="link" onClick={()=>{logout();go('/');}}>Sign out</button></>:<Link to="/auth">Sign in</Link>}</nav></header><Outlet/></div>}
