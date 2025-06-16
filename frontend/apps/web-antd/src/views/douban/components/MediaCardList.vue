<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';

import { Card, Flex } from 'ant-design-vue';

import { router } from '#/router';

const props = defineProps<{
  api: (params: any) => Promise<any>;
  params: Record<string, any>;
}>();

const mediaList = ref<any[]>([]);

onMounted(() => {
  props.api(props.params).then((_res) => {
    mediaList.value = _res;
  });
});

watch(props.params, () => {
  props.api(props.params).then((_res) => {
    mediaList.value = _res;
  });
});

const handleClick = (item: any) => {
  router.push({
    path: '/resource',
    query: {
      name: item.title,
    },
  });
};
</script>

<template>
  <Flex wrap="wrap" gap="middle" class="m-[20px]">
    <Card
      v-for="item in mediaList"
      :key="item.id"
      class="w-[160px]"
      @click="handleClick(item)"
    >
      <template #cover>
        <img
          :src="item.cover"
          class="h-[220px] w-full"
          :alt="item.card_subtitle"
        />
      </template>
      <Card.Meta :title="item.title">
        <template #description>
          <div class="line-clamp-2">{{ item.card_subtitle }}</div>
        </template>
      </Card.Meta>
    </Card>
  </Flex>
</template>
