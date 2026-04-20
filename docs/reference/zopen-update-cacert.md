<div v-pre class="man-page-content">


<h1 align="center">ZOPEN-UPDATE-CACERT</h1>




<h2>NAME
<a name="NAME"></a>
</h2>



<p style="margin-left:11%; margin-top: 1em">zopen-update-cacert
&minus; manual page for zopen-update-cacert 0.8.4</p>

<h2>DESCRIPTION
<a name="DESCRIPTION"></a>
</h2>



<p style="margin-left:11%; margin-top: 1em">zopen&minus;update&minus;cacert:
Update your cacert.pem file to the latest CA certificates
extracted from Mozilla.</p>


<p style="margin-left:11%; margin-top: 1em"><b>Syntax:</b></p>


<p style="margin-left:22%;">zopen&minus;update&minus;cacert
[&minus;fhv] [&lt;directory&gt;]</p>

<h2>OPTIONS
<a name="OPTIONS"></a>
</h2>



<p style="margin-left:11%; margin-top: 1em"><b>&minus;f</b>,
<b>&minus;&minus;force</b></p>

<p style="margin-left:22%;">update cacert.pem file even if
up to date.</p>

<p style="margin-left:11%;"><b>&minus;h</b>,
<b>&minus;&minus;help</b></p>

<p style="margin-left:22%;">print this help.</p>

<p style="margin-left:11%;"><b>&minus;i</b>,
<b>&minus;&minus;insecure&minus;fallback</b></p>

<p style="margin-left:22%;">(UNSAFE) Skip certificate
validation during download.</p>

<p style="margin-left:11%;"><b>&minus;v</b>,
<b>&minus;&minus;verbose</b></p>

<p style="margin-left:22%;">print verbose messages.</p>


<p style="margin-left:11%;"><b>&minus;&minus;version</b></p>

<p style="margin-left:22%;">print version.</p>


<p style="margin-left:11%; margin-top: 1em"><b>Parameters:</b></p>

<p style="margin-left:22%;">&lt;directory&gt;: the
directory where the cacert.pem will be updated.</p>

<p style="margin-left:22%; margin-top: 1em">The default
directory location is:
<i>/var/lib/jenkins/workspace/Port&minus;Update&minus;Nightly/meta_update</i></p>

<p style="margin-left:11%; margin-top: 1em">This is free
software: you are free to change and redistribute it under
the terms of the Apache License, Version 2.0.
&lt;https://www.apache.org/licenses/LICENSE&minus;2.0.html&gt;
There is NO WARRANTY, to the extent permitted by law.</p>

<h2>AUTHOR
<a name="AUTHOR"></a>
</h2>


<p style="margin-left:11%; margin-top: 1em">Written by
contributors to the zopen community.
&lt;https://github.com/zopencommunity/meta/graphs/contributors&gt;</p>

</div>

<style scoped>
.man-page-content {
  padding: 20px;
  line-height: 1.6;
  overflow-x: auto;
  background: var(--vp-c-bg-soft);
}

.man-page-content :deep(h1) {
  text-align: left;
}

.man-page-content :deep(h2) {
  margin-top: 1.5rem;
}

.man-page-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.man-page-content :deep(pre) {
  background: var(--vp-c-bg-soft);
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  white-space: pre-wrap;
}

.man-page-content :deep(p) {
  margin: 0.5rem 0;
}

.man-page-content :deep(a) {
  color: var(--vp-c-brand-1);
}
</style>
