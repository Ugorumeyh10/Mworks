import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import {
  createBlogPost,
  fetchBlogAdminPosts,
  publishBlogPost,
  runNewsAgent,
  unpublishBlogPost,
} from '../api/blog.js';
import { uploadKindFile } from '../api/listings.js';
import { getToken, getUser } from '../api/session.js';
import { BLOG_CATS, BlogCover } from './blogShared.jsx';
import './Blog.css';
import './Sell.css';

const EMPTY = { title: '', excerpt: '', body: '', category: 'Tech news', tags: '', youtube: '', publish: true };

export default function Newsroom() {
  const user = getUser();
  const authed = Boolean(getToken());
  const [rows, setRows] = useState([]);
  const [f, setF] = useState(EMPTY);
  const [media, setMedia] = useState([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [note, setNote] = useState('');

  const load = () => {
    fetchBlogAdminPosts()
      .then(setRows)
      .catch((err) => {
        setRows([]);
        setError(err.message || 'Could not load the newsroom.');
      });
  };

  useEffect(() => {
    if (!authed || !user?.isAdmin) return undefined;
    load();
    return undefined;
  }, [authed, user?.isAdmin]);

  if (!authed || !user?.isAdmin) {
    return (
      <div className="mk-page">
        <h1>Newsroom</h1>
        <div className="mk-empty">Admin access is required.</div>
      </div>
    );
  }

  const set = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setF((x) => ({ ...x, [k]: v }));
  };

  const addFiles = async (e) => {
    const files = [...(e.target.files || [])];
    e.target.value = '';
    if (!files.length) return;
    setError('');
    setBusy('upload');
    try {
      const added = [];
      for (const file of files) {
        const video = file.type.startsWith('video/');
        const key = await uploadKindFile(file, video ? 'blog_video' : 'blog_image');
        added.push({ kind: video ? 'video' : 'image', url: key });
      }
      setMedia((rows) => [...rows, ...added].slice(0, 6));
    } catch (err) {
      setError(err.message || 'Could not upload that file.');
    } finally {
      setBusy('');
    }
  };

  const write = async (e) => {
    e.preventDefault();
    setError('');
    if (f.title.trim().length < 4 || f.excerpt.trim().length < 10 || f.body.trim().length < 40) {
      setError('Give the post a title, a short excerpt, and a body.');
      return;
    }
    const payloadMedia = [...media];
    if (f.youtube.trim()) payloadMedia.push({ kind: 'youtube', url: f.youtube.trim() });
    setBusy('write');
    try {
      await createBlogPost({
        title: f.title.trim(),
        excerpt: f.excerpt.trim(),
        body: f.body.trim(),
        category: f.category,
        tags: f.tags.split(',').map((t) => t.trim()).filter(Boolean),
        media: payloadMedia,
        publish: f.publish,
      });
      setF(EMPTY);
      setMedia([]);
      setNote(f.publish ? 'Published.' : 'Saved as a draft.');
      load();
    } catch (err) {
      setError(err.message || 'Could not save that post.');
    } finally {
      setBusy('');
    }
  };

  const fetchNews = async () => {
    setError('');
    setNote('');
    setBusy('agent');
    try {
      const res = await runNewsAgent();
      setNote(`Agent published ${res.created} new ${res.created === 1 ? 'story' : 'stories'}. ${res.skipped} already on the blog.`);
      load();
    } catch (err) {
      setError(err.message || 'The news agent could not run.');
    } finally {
      setBusy('');
    }
  };

  const toggle = async (row) => {
    setBusy(row.id);
    setError('');
    try {
      if (row.status === 'published') await unpublishBlogPost(row.id);
      else await publishBlogPost(row.id);
      load();
    } catch (err) {
      setError(err.message || 'Could not update that post.');
    } finally {
      setBusy('');
    }
  };

  const drafts = rows.filter((r) => r.status === 'draft');
  const live = rows.filter((r) => r.status === 'published');

  return (
    <div className="blog-page newsroom">
      <div className="mk-head">
        <div>
          <h1>Newsroom</h1>
          <p className="sub">
            Write by hand with photos or video, or let the agent fetch tech news and publish it immediately.
          </p>
        </div>
        <div className="newsroom-actions">
          <Link to="/blog" className="mk-btn ghost">View blog</Link>
          <button type="button" className="mk-btn" onClick={fetchNews} disabled={busy === 'agent'}>
            <Icon name="bot" className="sm" />
            {busy === 'agent' ? 'Publishing news…' : 'Fetch latest tech news'}
          </button>
        </div>
      </div>

      {error && <p className="sf-err" role="alert">{error}</p>}
      {note && <p className="newsroom-note">{note}</p>}

      <div className="newsroom-grid">
        <form className="sell-form mk-card" onSubmit={write}>
          <h2 className="sell-h2 newsroom-h2">Write a post</h2>
          <div className="sf-row">
            <label className="sf-label" htmlFor="nr-title">Title</label>
            <input id="nr-title" type="text" value={f.title} onChange={set('title')} placeholder="e.g. What changed in Power Automate this week" />
          </div>
          <div className="sf-row">
            <label className="sf-label" htmlFor="nr-excerpt">Excerpt</label>
            <textarea id="nr-excerpt" rows="2" value={f.excerpt} onChange={set('excerpt')} placeholder="One friendly sentence for the card." />
          </div>
          <div className="sf-two">
            <div className="sf-row">
              <label className="sf-label" htmlFor="nr-cat">Category</label>
              <select id="nr-cat" value={f.category} onChange={set('category')}>
                {BLOG_CATS.filter((c) => c !== 'All').map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="sf-row">
              <label className="sf-label" htmlFor="nr-tags">Tags</label>
              <input id="nr-tags" type="text" value={f.tags} onChange={set('tags')} placeholder="RPA, AI" />
            </div>
          </div>
          <div className="sf-row">
            <label className="sf-label" htmlFor="nr-body">Body</label>
            <textarea id="nr-body" rows="10" value={f.body} onChange={set('body')} placeholder="Plain English. Use a blank line between paragraphs. Start a heading with ## ." />
          </div>
          <div className="sf-row">
            <span className="sf-label">Pictures and video</span>
            <label className="sf-file">
              <input type="file" accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm" multiple onChange={addFiles} hidden />
              {busy === 'upload' ? 'Uploading…' : 'Add photos or a video'}
            </label>
            <input type="url" value={f.youtube} onChange={set('youtube')} placeholder="YouTube link (optional)" />
            {media.length > 0 && (
              <div className="newsroom-thumbs">
                {media.map((item) => (
                  <span key={item.url} className="newsroom-thumb">{item.kind}</span>
                ))}
              </div>
            )}
          </div>
          <label className="newsroom-check">
            <input type="checkbox" checked={f.publish} onChange={set('publish')} />
            Publish now
          </label>
          <button type="submit" className="mk-btn" disabled={busy === 'write' || busy === 'upload'}>
            {f.publish ? 'Publish' : 'Save draft'}
          </button>
        </form>

        <div>
          <h2 className="sell-h2 newsroom-h2">Drafts ({drafts.length})</h2>
          {drafts.length === 0 ? (
            <div className="mk-empty">No drafts. Agent stories go live as soon as they are fetched.</div>
          ) : drafts.map((row) => (
            <div className="mk-card newsroom-row" key={row.id}>
              <BlogCover post={row} />
              <div className="sell-listing-title">
                {row.title}
                <span className="mk-pill warn">Draft</span>
              </div>
              <p className="body-text">{row.excerpt}</p>
              <div className="newsroom-row-actions">
                <Link to={`/blog/${row.id}`} className="mk-btn ghost sm">Preview</Link>
                <button type="button" className="mk-btn sm" disabled={busy === row.id} onClick={() => toggle(row)}>
                  Publish
                </button>
              </div>
            </div>
          ))}

          <h2 className="sell-h2">Live ({live.length})</h2>
          {live.map((row) => (
            <div className="mk-card newsroom-row" key={row.id}>
              <BlogCover post={row} />
              <div className="sell-listing-title">
                {row.title}
                <span className="mk-pill ok">{row.aiAssisted ? 'Agent' : 'Published'}</span>
              </div>
              <p className="body-text">{row.excerpt}</p>
              <div className="newsroom-row-actions">
                <Link to={`/blog/${row.id}`} className="mk-btn ghost sm">View</Link>
                <button type="button" className="mk-btn ghost sm" disabled={busy === row.id} onClick={() => toggle(row)}>
                  Unpublish
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
