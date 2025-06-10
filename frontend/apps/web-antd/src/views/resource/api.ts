import { requestClient } from '#/api/request';

/**
 * 资源搜索
 */
export const getResourceListApi = (params: any) => {
  return requestClient.get('/tg-resource/search', { params });
};
