import { requestClient } from '#/api/request';

/**
 * 获取定时任务列表
 */
export async function getCornTaskListApi() {
  return requestClient.get('/scheduled/tasks', {});
}

/**
 * 启用定时任务
 */
export async function enableCornTaskApi(taskName: string) {
  return requestClient.post(`/scheduled/tasks/${taskName}/enable`, {});
}

/**
 * 禁用定时任务
 */
export async function disableCornTaskApi(taskName: string) {
  return requestClient.post(`/scheduled/tasks/${taskName}/disable`, {});
}

/**
 * 删除定时任务
 */
export async function deleteCornTaskApi(taskName: string) {
  return requestClient.delete(`/scheduled/tasks/${taskName}`, {});
}

/**
 * 获取定时任务类型
 */
export async function getCornTaskTypeListApi() {
  return requestClient.get('/scheduled/task-types', {});
}

/**
 * 创建定时任务
 */
export async function createCornTaskApi(params: any) {
  return requestClient.post('/scheduled/tasks', params);
}

/**
 * 更新定时任务
 */
export async function updateCornTaskApi(params: any) {
  return requestClient.put(`/scheduled/tasks/${params.name}`, params);
}
