<script setup lang="ts">
import { ref, computed } from 'vue';
import { Button, message, Tag } from 'ant-design-vue';
import TaskEditor from '#/views/cornTask/components/TaskEditor.vue';
import { getTaskByUrl } from '#/views/utils';

const props = defineProps<{
  item: any;
}>();
const emit = defineEmits(['save']);

// 格式化时间为友好的时间间隔（如：几分钟前）
const formatTimeAgo = (dateStr: string) => {
  if (!dateStr) return '';
  try {
    // 处理日期字符串中的全角字符和空格
    const normalizedDate = dateStr.replace('：', ':').replace(' ', '');
    const targetDate = new Date(normalizedDate);
    if (isNaN(targetDate.getTime())) return '日期错误';
    
    const now = Date.now();
    const diffMs = now - targetDate.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const minute = 60;
    const hour = minute * 60;
    const day = hour * 24;
    
    // 时间间隔分级显示
    if (diffSec < minute) return `${diffSec}秒前`;
    if (diffSec < hour) return `${Math.floor(diffSec / minute)}分钟前`;
    
    const hours = Math.floor(diffSec / hour);
    const days = Math.floor(diffSec / day);
    
    // 大于23小时不显示分钟，按天和小时显示
    if (diffSec < day) {
      return `${hours}小时前`;
    } else {
      return `${days}天${hours % 24}小时前`;
    }
  } catch (error) {
    console.error('时间解析错误', error);
    return '解析失败';
  }
};

// 获取时间间隔对应的颜色类名
const getTimeColorClass = (dateStr: string) => {
  if (!dateStr) return '';
  try {
    const normalizedDate = dateStr.replace('：', ':').replace(' ', '');
    const targetDate = new Date(normalizedDate);
    if (isNaN(targetDate.getTime())) return '';
    
    const now = Date.now();
    const diffHour = Math.floor((now - targetDate.getTime()) / (1000 * 60 * 60));
    
    // 颜色分级逻辑
    if (diffHour < 6) return 'text-green-500';    // 小于6小时：绿色
    if (diffHour < 24) return 'text-blue-500';   // 24小时内：蓝色
    return 'text-red-500';                       // 超过24小时：红色
  } catch (error) {
    console.error('颜色计算错误', error);
    return '';
  }
};

// 计算时间显示内容和颜色类
const timeDisplay = computed(() => ({
  text: formatTimeAgo(props.item.pubDate),
  colorClass: getTimeColorClass(props.item.pubDate)
}));

// 跳转至链接
const onJump = () => {
  window.open(props.item.cloudLinks?.[0], '_blank');
};

// 触发保存事件
const onSave = () => {
  emit('save', props.item);
};

// 定时任务相关
const open = ref(false);
const currentTask = ref<any>({});
const onCreateTask = () => {
  const shareUrl = props.item.cloudLinks?.[0];
  if (shareUrl) {
    currentTask.value = {
      task: getTaskByUrl(shareUrl),
      name: props.item.keyword || props.item.title,
      params: { shareUrl }
    };
    open.value = true;
  } else {
    message.error('创建任务出错，没有分享链接');
  }
};
</script>

<template>
  <div class="rounded-lg border">
    <!-- 内容卡片头部：图片和文字 -->
    <div class="flex p-4 shadow-sm">
      <div class="w-1/3">
        <div class="relative pb-[150%]">
          <img
            :src="item.image"
            class="absolute inset-0 h-full w-full rounded-lg object-cover"
            alt="海报"
          />
          <Tag
            class="absolute left-[2px] top-[2px] z-10"
            color="blue"
            :bordered="false"
          >
            {{ item.cloudType }}
          </Tag>
        </div>
      </div>
      <div class="flex w-2/3 flex-col justify-between pl-4">
        <div>
          <h3 class="mb-2 truncate text-lg font-bold" :alt="item.title">
            {{ item.title?.indexOf('名称') === -1 ? item.title : item.title?.split('名称：')[1] }}
          </h3>
          <p class="mb-2 line-clamp-3 text-gray-600">
            {{ item.content }}
          </p>
          <p class="mb-2 line-clamp-3" :class="timeDisplay.colorClass">
            {{ timeDisplay.text }}
          </p>
        </div>
        <div class="text-sm text-gray-500">
          <p class="flex items-center overflow-hidden whitespace-nowrap">
            标签:
            <span class="ml-1 flex-1 overflow-hidden">
              <Tag
                v-for="tag in item.tags"
                :key="tag"
                :color="['pink', 'red', 'orange', 'cyan', 'blue', 'purple'][Math.floor(Math.random() * 6)]"
                class="mr-1 inline-block"
              >
                {{ tag }}
              </Tag>
            </span>
          </p>
        </div>
      </div>
    </div>
    
    <!-- 底部操作栏 -->
    <div class="h-[50px] w-full border-t text-right">
      <Button type="link" class="m-2" size="middle" @click="onJump">
        跳转
      </Button>
      <Button
        type="link"
        class="m-2"
        size="middle"
        @click="onSave"
        v-show="['quark', 'tianyiyun'].includes(item.cloudType)"
      >
        转存
      </Button>
      <Button type="link" class="m-2" size="middle" @click="onCreateTask">
        创建定时任务
      </Button>
    </div>
    
    <!-- 定时任务编辑组件 -->
    <TaskEditor v-model:open="open" :task="currentTask" />
  </div>
</template>

<!-- 自定义颜色样式 -->
<style scoped>
.text-green-500 { color: #10b981; }  /* 绿色：小于6小时 */
.text-blue-500 { color: #3b82f6; }   /* 蓝色：24小时内 */
.text-red-500 { color: #ef4444; }    /* 红色：超过24小时 */
</style>