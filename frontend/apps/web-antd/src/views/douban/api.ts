import { requestClient } from '#/api/request';

/**
 * 登录
 */
export async function getHotMovieListApi(params: any) {
  return requestClient.get('/douban/hot_list', { params });
}
