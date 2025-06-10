<script setup lang="ts">
import { onMounted } from 'vue';

import { getResourceListApi } from './api';

onMounted(async () => {
  const res = await getResourceListApi({
    keyword: '会计刺客2',
  });
  console.error(res);
});
</script>

<template>资源搜索</template>
