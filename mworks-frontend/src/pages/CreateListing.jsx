import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Icon from '../components/Icon.jsx';
import { categories, commissionRate, money } from '../data/marketplace.js';
import { createListing, publishListing, uploadListingFile } from '../api/listings.js';
import { apiEnabled } from '../api/client.js';
import { getToken } from '../api/session.js';
import './Sell.css';

const PLATFORMS = ['Power Automate', 'Python', 'UiPath', 'Automation Anywhere', 'Other'];
const MODELS = ['DeepSeek', 'GPT-4o', 'Claude', 'Gemini', 'Llama'];

export default function CreateListing() {
  const navigate = useNavigate();
  const [type, setType] = useState('automation');
  const [f, setF] = useState({
    title: '', category: '', blurb: '', description: '', price: '', tags: '',
    platform: 'Power Automate', packageName: '', videoName: '',
    models: ['GPT-4o'], promptCount: '', promptText: '', sampleInput: '', sampleOutput: '',
    license: 'template', attest: false,
  });
  const [metrics, setMetrics] = useState([
    { label: '', value: '' },
    { label: '', value: '' },
    { label: '', value: '' },
  ]);
  const [errors, setErrors] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [packFile, setPackFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState(null);
  const [publishing, setPublishing] = useState(false);

  const set = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setF((x) => ({ ...x, [k]: v }));
    setErrors((x) => ({ ...x, [k]: undefined }));
  };
  const setFile = (e) => {
    const file = e.target.files?.[0] || null;
    setPackFile(file);
    setF((x) => ({ ...x, packageName: file?.name || '' }));
    setErrors((x) => ({ ...x, packageName: undefined }));
  };
  const toggleModel = (m) =>
    setF((x) => ({ ...x, models: x.models.includes(m) ? x.models.filter((y) => y !== m) : [...x.models, m] }));
  const setMetric = (i, key) => (e) =>
    setMetrics((rows) => rows.map((r, j) => (j === i ? { ...r, [key]: e.target.value } : r)));

  const priceNum = parseFloat(f.price) || 0;
  const rate = commissionRate(type);
  const youGet = priceNum * (1 - rate);

  const submit = async (e) => {
    e.preventDefault();
    const next = {};
    if (f.title.trim().length < 4) next.title = 'Give your listing a clear title.';
    if (!f.category) next.category = 'Pick a category.';
    if (f.blurb.trim().length < 10) next.blurb = 'Add a one-line summary.';
    if (f.description.trim().length < 30) next.description = 'Describe what it does in a bit more detail.';
    if (!(priceNum > 0)) next.price = 'Set a price above ₦0.';
    if (!f.attest) next.attest = 'You must confirm this before submitting.';
    if (type === 'automation' && !packFile) next.packageName = 'Upload the automation package.';
    if (type === 'prompt') {
      if (f.models.length === 0) next.models = 'Select at least one target model.';
      if (f.promptText.trim().length < 20) next.promptText = 'Paste the prompt text.';
      if (f.sampleOutput.trim().length < 20) next.sampleOutput = 'Add a sample output for the buyer preview.';
    }
    if (type === 'agent') {
      if (f.promptText.trim().length < 20) next.promptText = 'Paste the interviewer playbook.';
    }
    if (type === 'document' && !packFile) next.packageName = 'Upload the document pack.';
    const maxBytes = type === 'document' ? 12 * 1024 * 1024 : 20 * 1024 * 1024;
    if (packFile && packFile.size > maxBytes) {
      next.packageName = type === 'document' ? 'Keep the pack under 12 MB.' : 'Keep the package under 20 MB.';
    }
    setErrors(next);
    if (Object.keys(next).length !== 0) return;
    if (apiEnabled() && getToken()) {
      setBusy(true);
      try {
        let object_key;
        if (packFile && (type === 'document' || type === 'automation')) {
          object_key = await uploadListingFile(packFile, type);
        }
        const row = await createListing({
          type,
          title: f.title.trim(),
          blurb: f.blurb.trim(),
          description: f.description.trim(),
          category: f.category,
          price_value: Math.round(priceNum),
          tags: f.tags.split(',').map((t) => t.trim()).filter(Boolean),
          platform: type === 'automation' ? f.platform : undefined,
          models: type === 'prompt' || type === 'agent' ? (f.models.length ? f.models : ['DeepSeek']) : [],
          prompt_count: (type === 'prompt' || type === 'agent') && f.promptCount ? Number(f.promptCount) : undefined,
          prompt_text: type === 'prompt' || type === 'agent' ? f.promptText.trim() : undefined,
          metrics: type === 'automation' ? metrics.filter((m) => m.label && m.value) : [],
          license: type === 'document' ? f.license : undefined,
          object_key,
        });
        try {
          const verified = await publishListing(row.id);
          setCreated(verified);
        } catch {
          setCreated(row);
        }
        setSubmitted(true);
      } catch (err) {
        setErrors({ attest: err.message || 'Could not submit the listing.' });
      } finally {
        setBusy(false);
      }
      return;
    }
    setSubmitted(true);
  };

  const goLive = async () => {
    if (!created?.id) {
      navigate('/sell');
      return;
    }
    setPublishing(true);
    try {
      const next = await publishListing(created.id);
      setCreated(next);
      if (next.status === 'live') {
        navigate(`/listing/${created.id}`);
        return;
      }
      setErrors({ attest: 'Verification did not pass. Fix the pack and run it again.' });
    } catch (err) {
      setErrors({ attest: err.message || 'Could not run verification.' });
    } finally {
      setPublishing(false);
    }
  };

  if (submitted) {
    return (
      <div className="mk-page mk-narrow">
        <div className="submitted">
          <span className="submitted-icon"><Icon name="shield" /></span>
          <h1>
            {created?.status === 'live'
              ? 'Verified and live'
              : created?.status === 'rejected'
                ? 'Verification did not pass'
                : 'Saved, waiting on verification'}
          </h1>
          <p>
            {created?.status === 'live'
              ? <><strong>{f.title}</strong> passed checks and is on the public catalog.</>
              : created?.status === 'rejected'
                ? <><strong>{f.title}</strong> stayed private. Review the log, fix the pack, and run verification again.</>
                : <><strong>{f.title}</strong> is on your seller dashboard. Buyers will not see it until verification passes.</>}
          </p>
          {created?.verificationLog?.length > 0 && (
            <div className="submitted-log">
              {created.verificationLog.map((v, i) => (
                <div className="vrow" key={`${v.label}-${i}`}>
                  <span>{v.label}</span>
                  <span className={String(v.status).toLowerCase().includes('fail') ? 'bad' : 'ok'}>{v.status}</span>
                </div>
              ))}
            </div>
          )}
          {errors.attest && <span className="sf-err">{errors.attest}</span>}
          <div className="submitted-actions">
            {created?.status !== 'live' && (
              <button type="button" className="mk-btn" onClick={goLive} disabled={publishing}>
                {publishing ? 'Checking…' : 'Run verification'}
              </button>
            )}
            {created?.status === 'live' && (
              <>
                <Link to={`/listing/${created.id}`} className="mk-btn">View listing</Link>
                {type === 'agent' && (
                  <Link to={`/interviewer?listing=${created.id}`} className="mk-btn ghost">Open console</Link>
                )}
              </>
            )}
            <Link to="/sell" className="mk-btn ghost">Seller dashboard</Link>
            <button className="mk-btn ghost" onClick={() => { setSubmitted(false); setCreated(null); setPackFile(null); setF((x) => ({ ...x, title: '', blurb: '', description: '', price: '', packageName: '' })); }}>
              Create another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mk-page mk-narrow">
      <Link to="/sell" className="mk-back"><Icon name="arrow-left" className="sm" /> Seller dashboard</Link>
      <div className="mk-head">
        <div>
          <h1>New listing</h1>
          <p className="sub">List an automation, prompt pack, document pack, or AI interviewer. It stays private until originality or sandbox checks pass.</p>
        </div>
      </div>

      <form className="sell-form" onSubmit={submit} noValidate>
        <div className="sf-row">
          <span className="sf-label">Listing type</span>
          <div className="mk-seg">
            <button type="button" className={type === 'automation' ? 'on' : ''} onClick={() => setType('automation')}>
              Automation / bot
            </button>
            <button type="button" className={type === 'prompt' ? 'on' : ''} onClick={() => setType('prompt')}>
              Prompt / prompt pack
            </button>
            <button type="button" className={type === 'document' ? 'on' : ''} onClick={() => setType('document')}>
              Document pack
            </button>
            <button type="button" className={type === 'agent' ? 'on' : ''} onClick={() => setType('agent')}>
              AI interviewer
            </button>
          </div>
          <span className="sf-hint">
            {type === 'automation'
              ? 'Verified by sandbox execution. Commission 15%.'
              : type === 'document'
                ? 'Verified by originality and redaction check. Commission 10%. Revise orders capped at ₦25,000.'
                : type === 'agent'
                  ? 'Hosted interviewer. Buyers trial, buy, or hire. Commission 15%. The agent must disclose it is AI.'
                  : 'Verified by originality check. Commission 10%.'}
          </span>
        </div>

        <div className={'sf-row' + (errors.title ? ' bad' : '')}>
          <label className="sf-label" htmlFor="title">Title</label>
          <input id="title" type="text" value={f.title} onChange={set('title')}
            placeholder={type === 'automation' ? 'e.g. Invoice Reconciliation Bot' : type === 'document' ? 'e.g. RPA Opportunity Canvas' : type === 'agent' ? 'e.g. Banking RPA Interviewer' : 'e.g. Customer Support Prompt Pack'} />
          {errors.title && <span className="sf-err">{errors.title}</span>}
        </div>

        <div className="sf-two">
          <div className={'sf-row' + (errors.category ? ' bad' : '')}>
            <label className="sf-label" htmlFor="category">Category</label>
            <select id="category" value={f.category} onChange={set('category')}>
              <option value="">Select…</option>
              {categories.map((c) => <option key={c}>{c}</option>)}
            </select>
            {errors.category && <span className="sf-err">{errors.category}</span>}
          </div>
          <div className={'sf-row' + (errors.price ? ' bad' : '')}>
            <label className="sf-label" htmlFor="price">Price (₦)</label>
            <input id="price" type="number" min="0" step="1" value={f.price} onChange={set('price')} placeholder="0" />
            {errors.price && <span className="sf-err">{errors.price}</span>}
          </div>
        </div>

        {priceNum > 0 && (
          <div className="fee-preview">
            <span>Buyer pays <b>{money(priceNum)}</b></span>
            <span>Mworks commission ({Math.round(rate * 100)}%) −{money(priceNum * rate)}</span>
            <span className="fee-net">You receive <b>{money(youGet)}</b></span>
          </div>
        )}

        <div className={'sf-row' + (errors.blurb ? ' bad' : '')}>
          <label className="sf-label" htmlFor="blurb">One-line summary</label>
          <input id="blurb" type="text" value={f.blurb} onChange={set('blurb')}
            placeholder="Shown on the browse card" />
          {errors.blurb && <span className="sf-err">{errors.blurb}</span>}
        </div>

        <div className={'sf-row' + (errors.description ? ' bad' : '')}>
          <label className="sf-label" htmlFor="description">Description</label>
          <textarea id="description" rows="4" value={f.description} onChange={set('description')}
            placeholder="What it does, what it needs to run, what the buyer gets." />
          {errors.description && <span className="sf-err">{errors.description}</span>}
        </div>

        <div className="sf-row">
          <label className="sf-label" htmlFor="tags">Tags</label>
          <input id="tags" type="text" value={f.tags} onChange={set('tags')} placeholder="Comma separated, e.g. Finance, Power Automate" />
        </div>

        {type === 'automation' ? (
          <>
            <div className="sf-two">
              <div className="sf-row">
                <label className="sf-label" htmlFor="platform">Platform</label>
                <select id="platform" value={f.platform} onChange={set('platform')}>
                  {PLATFORMS.map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
              <div className={'sf-row' + (errors.packageName ? ' bad' : '')}>
                <span className="sf-label">Automation package</span>
                <label className="sf-file">
                  <Icon name="upload" className="sm" />
                  {f.packageName || 'Upload .zip / .xml'}
                  <input type="file" accept=".zip,.xml" onChange={setFile} hidden />
                </label>
                {errors.packageName && <span className="sf-err">{errors.packageName}</span>}
              </div>
            </div>

            <div className="sf-row">
              <span className="sf-label">Video demo</span>
              <label className="sf-file">
                <Icon name="upload" className="sm" />
                {f.videoName || 'Upload a short screen recording'}
                <input type="file" accept="video/*" onChange={(e) => setF((x) => ({ ...x, videoName: e.target.files?.[0]?.name || '' }))} hidden />
              </label>
            </div>

            <div className="sf-row">
              <span className="sf-label">Declared performance metrics</span>
              <span className="sf-hint">The sandbox checks these against a real run.</span>
              {metrics.map((m, i) => (
                <div className="metric-input" key={i}>
                  <input type="text" placeholder="Metric (e.g. Error reduction)" value={m.label} onChange={setMetric(i, 'label')} />
                  <input type="text" placeholder="Value (e.g. 92%)" value={m.value} onChange={setMetric(i, 'value')} />
                </div>
              ))}
            </div>
          </>
        ) : type === 'document' ? (
          <>
            <div className="sf-two">
              <div className="sf-row">
                <label className="sf-label" htmlFor="license">License</label>
                <select id="license" value={f.license} onChange={set('license')}>
                  <option value="template">Template (reuse)</option>
                  <option value="exclusive">Exclusive (one buyer)</option>
                  <option value="revise_rights">Includes revise rights</option>
                </select>
              </div>
              <div className={'sf-row' + (errors.packageName ? ' bad' : '')}>
                <span className="sf-label">Document pack</span>
                <label className="sf-file">
                  <Icon name="upload" className="sm" />
                  {f.packageName || 'Upload .pdf / .docx / .md (max 25 MB)'}
                  <input type="file" accept=".pdf,.docx,.md,.txt" onChange={setFile} hidden />
                </label>
                {errors.packageName && <span className="sf-err">{errors.packageName}</span>}
              </div>
            </div>
            <p className="sf-hint">Buyers see a two-page watermarked preview. The full file unlocks after escrow.</p>
          </>
        ) : type === 'agent' ? (
          <>
            <div className={'sf-row' + (errors.models ? ' bad' : '')}>
              <span className="sf-label">Works with</span>
              <div className="sf-checks">
                {MODELS.map((m) => (
                  <label key={m} className={'sf-chip' + (f.models.includes(m) ? ' on' : '')}>
                    <input type="checkbox" checked={f.models.includes(m)} onChange={() => toggleModel(m)} hidden />
                    {m}
                  </label>
                ))}
              </div>
              {errors.models && <span className="sf-err">{errors.models}</span>}
            </div>
            <div className="sf-row">
              <label className="sf-label" htmlFor="promptCount">Max questions (optional)</label>
              <input id="promptCount" type="number" min="1" value={f.promptCount} onChange={set('promptCount')} placeholder="6" />
            </div>
            <div className={'sf-row' + (errors.promptText ? ' bad' : '')}>
              <label className="sf-label" htmlFor="promptText">Interviewer playbook</label>
              <textarea id="promptText" rows="6" value={f.promptText} onChange={set('promptText')}
                placeholder="Rubric and topics. Example: Ask about Power Automate testing and secrets handling. Never claim to be a human. Do not make a hire decision." />
              {errors.promptText && <span className="sf-err">{errors.promptText}</span>}
            </div>
            <p className="sf-hint">
              Buyers get a hosted license plus this playbook to download. Mworks still forces AI disclosure, consent, and no code execution.
            </p>
          </>
        ) : (
          <>
            <div className={'sf-row' + (errors.models ? ' bad' : '')}>
              <span className="sf-label">Target model(s)</span>
              <div className="sf-checks">
                {MODELS.map((m) => (
                  <label key={m} className={'sf-chip' + (f.models.includes(m) ? ' on' : '')}>
                    <input type="checkbox" checked={f.models.includes(m)} onChange={() => toggleModel(m)} hidden />
                    {m}
                  </label>
                ))}
              </div>
              {errors.models && <span className="sf-err">{errors.models}</span>}
            </div>

            <div className="sf-two">
              <div className="sf-row">
                <label className="sf-label" htmlFor="promptCount">Prompts in pack</label>
                <input id="promptCount" type="number" min="1" value={f.promptCount} onChange={set('promptCount')} placeholder="1" />
              </div>
            </div>

            <div className={'sf-row' + (errors.promptText ? ' bad' : '')}>
              <label className="sf-label" htmlFor="promptText">Prompt text / template</label>
              <textarea id="promptText" rows="4" value={f.promptText} onChange={set('promptText')}
                placeholder="The full prompt or system-prompt template. Buyers see this only after purchase." />
              {errors.promptText && <span className="sf-err">{errors.promptText}</span>}
            </div>

            <div className="sf-two">
              <div className="sf-row">
                <label className="sf-label" htmlFor="sampleInput">Sample input</label>
                <textarea id="sampleInput" rows="3" value={f.sampleInput} onChange={set('sampleInput')} placeholder="Example input" />
              </div>
              <div className={'sf-row' + (errors.sampleOutput ? ' bad' : '')}>
                <label className="sf-label" htmlFor="sampleOutput">Sample output (public preview)</label>
                <textarea id="sampleOutput" rows="3" value={f.sampleOutput} onChange={set('sampleOutput')} placeholder="What it produces" />
                {errors.sampleOutput && <span className="sf-err">{errors.sampleOutput}</span>}
              </div>
            </div>
          </>
        )}

        <label className={'sf-attest' + (errors.attest ? ' bad' : '')}>
          <input type="checkbox" checked={f.attest} onChange={set('attest')} />
          <span>
            {type === 'automation'
              ? 'I own the rights to this automation, it contains no production credentials or customer data, and I consent to sandboxed execution for verification.'
              : type === 'document'
                ? 'This pack is my original work, it contains no client names or production data, and I consent to originality and redaction checks.'
                : type === 'agent'
                  ? 'This interviewer is my original playbook. It will disclose it is AI, never impersonate a human, and never execute candidate code.'
                  : 'This prompt is my original work and is not copied or scraped from another marketplace or public dataset.'}
          </span>
        </label>
        {errors.attest && <span className="sf-err">{errors.attest}</span>}

        <div className="sf-submit-row">
          <button type="submit" className="mk-btn" disabled={busy}>{busy ? 'Uploading…' : 'Save listing'}</button>
          <Link to="/sell" className="mk-btn ghost">Cancel</Link>
        </div>
      </form>
    </div>
  );
}
