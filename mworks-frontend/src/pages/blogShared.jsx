import Icon from '../components/Icon.jsx';

export const BLOG_CATS = ['All', 'Tech news', 'Playbooks', 'Product', 'Announcements'];

export function youtubeId(url) {
  const match = String(url || '').match(/(?:youtu\.be\/|v=|embed\/|shorts\/)([A-Za-z0-9_-]{11})/);
  return match ? match[1] : '';
}

export function AiBadge({ post }) {
  if (!post?.aiAssisted) return null;
  return (
    <span className="blog-ai">
      <Icon name="bot" className="sm" />
      Drafted by the news agent
    </span>
  );
}

export function BlogCover({ post, className = '' }) {
  const src = post?.coverUrl;
  if (!src) return null;
  return (
    <div className={`blog-cover ${className}`}>
      <img src={src} alt="" loading="lazy" />
    </div>
  );
}

export function BlogMedia({ items = [] }) {
  if (!items.length) return null;
  return (
    <div className="blog-media">
      {items.map((item) => {
        if (item.kind === 'youtube') {
          const id = youtubeId(item.url);
          if (!id) return null;
          return (
            <div className="blog-video" key={item.url}>
              <iframe
                src={`https://www.youtube-nocookie.com/embed/${id}`}
                title="Video"
                allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          );
        }
        if (item.kind === 'video') {
          return (
            <video className="blog-file-video" key={item.url} src={item.url} controls playsInline />
          );
        }
        return <img className="blog-photo" key={item.url} src={item.url} alt="" loading="lazy" />;
      })}
    </div>
  );
}

export function BlogBody({ text, midSlot = null }) {
  const blocks = (text || '').split(/\n{2,}/).map((b) => b.trim()).filter(Boolean);
  const nodes = [];
  let paras = 0;
  blocks.forEach((block, i) => {
    if (block.startsWith('## ')) {
      nodes.push(<h2 key={i}>{block.slice(3)}</h2>);
    } else {
      paras += 1;
      nodes.push(
        <p key={i}>
          {block.split('\n').map((line, j) => (j === 0 ? line : [<br key={j} />, line]))}
        </p>,
      );
      if (midSlot && paras === 2 && i < blocks.length - 1) {
        nodes.push(<div key="mid-ad">{midSlot}</div>);
      }
    }
  });
  return <div className="blog-prose">{nodes}</div>;
}
