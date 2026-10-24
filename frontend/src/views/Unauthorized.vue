<template>
  <div class="state-box">
    <h3>403 &mdash; Not authorized</h3>
    <p>Your account role does not have access to this page.</p>
    <router-link class="btn btn-primary" :to="{ name: 'dashboard' }">Back to dashboard</router-link>
  </div>
</template>
