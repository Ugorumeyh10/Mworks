import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppShell from './components/AppShell.jsx';
import IconSprite from './components/IconSprite.jsx';
import Landing from './pages/Landing.jsx';
import Login from './pages/Login.jsx';
import Signup from './pages/Signup.jsx';
import DiscoverFeed from './pages/DiscoverFeed.jsx';
import Browse from './pages/Browse.jsx';
import Listing from './pages/Listing.jsx';
import CreateListing from './pages/CreateListing.jsx';
import SellerDashboard from './pages/SellerDashboard.jsx';
import TrustClaims from './pages/TrustClaims.jsx';
import Checkout from './pages/Checkout.jsx';
import PayLocal from './pages/PayLocal.jsx';
import Orders from './pages/Orders.jsx';
import OrderDetail from './pages/OrderDetail.jsx';
import Profile from './pages/Profile.jsx';
import SettingsProfile from './pages/SettingsProfile.jsx';
import Notifications from './pages/Notifications.jsx';
import JobAgent from './pages/JobAgent.jsx';
import JobBoard from './pages/JobBoard.jsx';
import JobDetail from './pages/JobDetail.jsx';
import MyApplications from './pages/MyApplications.jsx';
import PostJob from './pages/PostJob.jsx';
import InterviewerHub from './pages/InterviewerHub.jsx';
import InterviewerLive from './pages/InterviewerLive.jsx';
import Talent from './pages/Talent.jsx';
import PartnerProfile from './pages/PartnerProfile.jsx';
import PartnerApply from './pages/PartnerApply.jsx';
import Messages from './pages/Messages.jsx';
import Assistant from './pages/Assistant.jsx';
import Blog from './pages/Blog.jsx';
import BlogPost from './pages/BlogPost.jsx';
import Newsroom from './pages/Newsroom.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <IconSprite />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route element={<AppShell />}>
          <Route path="/discover" element={<DiscoverFeed />} />
          <Route path="/browse" element={<Browse />} />
          <Route path="/listing/:id" element={<Listing />} />
          <Route path="/sell" element={<SellerDashboard />} />
          <Route path="/sell/claims" element={<TrustClaims />} />
          <Route path="/sell/new" element={<CreateListing />} />
          <Route path="/checkout/pay/:id" element={<PayLocal />} />
          <Route path="/checkout/:id" element={<Checkout />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/orders/:id" element={<OrderDetail />} />
          <Route path="/u/:handle" element={<Profile />} />
          <Route path="/settings/profile" element={<SettingsProfile />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/jobs" element={<JobAgent />} />
          <Route path="/jobs/board" element={<JobBoard />} />
          <Route path="/jobs/board/:id" element={<JobDetail />} />
          <Route path="/jobs/applications" element={<MyApplications />} />
          <Route path="/jobs/post" element={<PostJob />} />
          <Route path="/interviewer" element={<InterviewerHub />} />
          <Route path="/interviewer/s/:id" element={<InterviewerLive />} />
          <Route path="/talent" element={<Talent />} />
          <Route path="/partners/apply" element={<PartnerApply />} />
          <Route path="/partners/:id" element={<PartnerProfile />} />
          <Route path="/messages" element={<Messages />} />
          <Route path="/assistant" element={<Assistant />} />
          <Route path="/blog" element={<Blog />} />
          <Route path="/blog/newsroom" element={<Newsroom />} />
          <Route path="/blog/:slug" element={<BlogPost />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
