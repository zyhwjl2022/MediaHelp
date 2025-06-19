<script setup lang="ts">
import { onActivated, onMounted, onUnmounted, ref } from 'vue';

import { Form, FormItem, Select, Tag } from 'ant-design-vue';
import dayjs from 'dayjs';

import { getCornTaskListApi, getLogListApi } from './api';

const taskList = ref<any>([]);
const taskName = ref('');
const refreshTaskList = () => {
  getCornTaskListApi().then((res: any) => {
    taskList.value = (res || []).map((item: any) => ({
      label: `${item.name} (${item.task})`,
      value: `${item.name} (${item.task})`,
    }));
  });
};

const convertLevel = (level: string) => {
  if (level === 'INFO') {
    return 'success';
  }
  if (level === 'ERROR') {
    return 'error';
  }
  if (level === 'WARN') {
    return 'warning';
  }
  return 'default';
};

const logList = ref<any>([]);
const refreshLogList = () => {
  getLogListApi({ message_contains: taskName.value }).then((res) => {
    const { items } = res;
    logList.value = items || [];
  });
};

let IntervalKey: NodeJS.Timeout | null = null;
onMounted(() => {
  refreshLogList();
  refreshTaskList();
  IntervalKey = setInterval(() => {
    refreshLogList();
  }, 3000);
});
onActivated(() => {
  refreshTaskList();
  refreshLogList();
});
onUnmounted(() => {
  if (IntervalKey) {
    clearInterval(IntervalKey);
  }
});
</script>
<template>
  <div class="m-4 h-full">
    <Form layout="inline">
      <FormItem label="任务" name="module" class="w-[500px]">
        <Select v-model:value="taskName" @change="refreshLogList" allow-clear>
          <Select.Option
            v-for="item in taskList"
            :key="item.value"
            :value="item.value"
          >
            {{ item.label }}
          </Select.Option>
        </Select>
      </FormItem>
    </Form>
    <div class="mt-4 h-[calc(100vh-170px)] overflow-y-auto bg-black p-2">
      <div v-for="item in logList" :key="item.id">
        <Tag :color="convertLevel(item.level)">{{ item.level }}</Tag>
        <span class="ml-2 text-green-400">{{
          dayjs(item.timestamp).format('YYYY-MM-DD HH:mm:ss')
        }}</span>
        <pre class="ml-2">{{ item.message }}</pre>
      </div>
    </div>
  </div>
</template>
