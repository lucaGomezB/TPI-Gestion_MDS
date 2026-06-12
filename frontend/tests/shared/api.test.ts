import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '../../src/shared/services/api';
import * as refreshQueue from '../../src/shared/services/refreshQueue';

describe('API configuration', () => {
  it('has the correct base URL', () => {
    expect(api.defaults.baseURL).toBe('/api');
  });

  it('sets Content-Type header to application/json', () => {
    expect(api.defaults.headers['Content-Type']).toBe('application/json');
  });

  it('has a request interceptor installed', () => {
    const count = api.interceptors.request.handlers.length;
    expect(count).toBeGreaterThan(0);
  });

  it('has a response interceptor installed', () => {
    const count = api.interceptors.response.handlers.length;
    expect(count).toBeGreaterThan(0);
  });
});

describe('refreshQueue', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('executes the refresh function and returns result', async () => {
    const refreshFn = vi.fn().mockResolvedValue('new-token');
    const result = await refreshQueue.enqueueRefresh(refreshFn);
    expect(result).toBe('new-token');
    expect(refreshFn).toHaveBeenCalledTimes(1);
  });

  it('returns the in-flight promise when refresh is already queued', async () => {
    const refreshFn = vi.fn().mockResolvedValue('new-token');

    const promise1 = refreshQueue.enqueueRefresh(refreshFn);
    const promise2 = refreshQueue.enqueueRefresh(refreshFn);

    const [result1, result2] = await Promise.all([promise1, promise2]);
    expect(result1).toBe('new-token');
    expect(result2).toBe('new-token');
    expect(refreshFn).toHaveBeenCalledTimes(1);
  });

  it('clears the queue after refresh completes', async () => {
    const refreshFn = vi.fn().mockResolvedValue('new-token');

    await refreshQueue.enqueueRefresh(refreshFn);
    expect(refreshFn).toHaveBeenCalledTimes(1);

    // Second call should start a new refresh
    await refreshQueue.enqueueRefresh(refreshFn);
    expect(refreshFn).toHaveBeenCalledTimes(2);
  });

  it('clears the queue after refresh fails', async () => {
    const refreshFn = vi.fn().mockRejectedValue(new Error('refresh failed'));

    await expect(refreshQueue.enqueueRefresh(refreshFn)).rejects.toThrow('refresh failed');

    // Next call should retry, not reuse the failed promise
    const refreshFn2 = vi.fn().mockResolvedValue('recovered');
    const result = await refreshQueue.enqueueRefresh(refreshFn2);
    expect(result).toBe('recovered');
  });
});
