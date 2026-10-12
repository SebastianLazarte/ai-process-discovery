// The only module that talks to the network (RS-49). Every call names an endpoint from
// ENDPOINTS; tests/unit/test_web_client.py checks each one against the OpenAPI schema.

export const ENDPOINTS = {
  listProcesses: ['GET', '/processes'],
  createProcess: ['POST', '/processes'],
  getProcess: ['GET', '/processes/{process_id}'],
  updateProcess: ['PATCH', '/processes/{process_id}'],
  deleteProcess: ['DELETE', '/processes/{process_id}'],
  addStep: ['POST', '/processes/{process_id}/steps'],
  reorderSteps: ['PUT', '/processes/{process_id}/steps/order'],
  updateStep: ['PATCH', '/steps/{step_id}'],
  deleteStep: ['DELETE', '/steps/{step_id}'],
  listDemos: ['GET', '/demo-processes'],
  loadDemo: ['POST', '/demo-processes/{slug}'],
  runAnalysis: ['POST', '/processes/{process_id}/analyses'],
  listAnalyses: ['GET', '/processes/{process_id}/analyses'],
  getAnalysis: ['GET', '/analyses/{analysis_id}'],
  addOverride: ['POST', '/analyses/{analysis_id}/overrides'],
  getBlueprint: ['GET', '/analyses/{analysis_id}/blueprint'],
  getBlueprintMarkdown: ['GET', '/analyses/{analysis_id}/blueprint.md'],
};

export class ApiError extends Error {
  constructor(status, message, fields = {}) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

export function fillPath(template, params = {}) {
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    if (params[key] === undefined) throw new Error(`missing path parameter ${key}`);
    return encodeURIComponent(params[key]);
  });
}

// Turns an error body into a message and per-field messages. Two shapes reach the
// client: domain errors ({detail, field}) and request validation ({detail: [{loc, msg}]}).
export function describeError(status, body) {
  const detail = body?.detail;
  if (Array.isArray(detail)) {
    const fields = {};
    for (const item of detail) {
      const name = item.loc?.filter(part => part !== 'body').map(String).join('.') || 'request';
      fields[name] = item.msg;
    }
    return { message: 'Check the highlighted fields.', fields };
  }
  const message = typeof detail === 'string' && detail ? detail : `Request failed (${status}).`;
  return { message, fields: body?.field ? { [body.field]: message } : {} };
}

export async function call(name, params = {}, body = undefined) {
  const [method, template] = ENDPOINTS[name];
  let response;
  try {
    response = await fetch(fillPath(template, params), {
      method,
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, 'The API cannot be reached. Is the server running?');
  }
  if (response.status === 204) return null;
  const isJson = (response.headers.get('content-type') || '').includes('application/json');
  const payload = isJson ? await response.json() : await response.text();
  if (!response.ok) {
    const { message, fields } = describeError(response.status, isJson ? payload : { detail: payload });
    throw new ApiError(response.status, message, fields);
  }
  return payload;
}
