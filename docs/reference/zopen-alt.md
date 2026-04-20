<div v-pre class="man-page-content">


<h1 align="center">ZOPEN-ALT</h1>




<h2>NAME
<a name="NAME"></a>
</h2>


<p style="margin-left:11%; margin-top: 1em">zopen-alt
&minus; manual page for zopen-alt 0.8.4</p>

<h2>SYNOPSIS
<a name="SYNOPSIS"></a>
</h2>



<p style="margin-left:11%; margin-top: 1em"><b>zopen-alt</b>
[<i>OPTION</i>] [<i>PACKAGE</i>] [<i>PARAMETERS</i>]...</p>

<h2>DESCRIPTION
<a name="DESCRIPTION"></a>
</h2>



<p style="margin-left:11%; margin-top: 1em">zopen&minus;alt
is a utility for zopen community to switch package versions
for currently installed packages.</p>

<h2>OPTIONS
<a name="OPTIONS"></a>
</h2>



<p style="margin-left:11%; margin-top: 1em"><b>&minus;h</b>,
<b>&minus;&minus;help</b>, &minus;?</p>

<p style="margin-left:22%;">display this help and exit.</p>

<p style="margin-left:11%;"><b>&minus;&minus;select</b>
[PACKAGE]</p>

<p style="margin-left:22%;">select the active version for
PACKAGE from a list.</p>

<p style="margin-left:11%;"><b>&minus;s</b>,
<b>&minus;&minus;set</b> [PACKAGE] [VERSION]</p>

<p style="margin-left:22%;">set the active version for
PACKAGE to VERSION.</p>

<p style="margin-left:11%;"><b>&minus;v</b>,
<b>&minus;&minus;verbose</b></p>

<p style="margin-left:22%;">run in verbose mode.</p>


<p style="margin-left:11%;"><b>&minus;&minus;version</b></p>

<p style="margin-left:22%;">print version</p>

<h2>EXAMPLES
<a name="EXAMPLES"></a>
</h2>


<p style="margin-left:11%; margin-top: 1em">zopen alt
foo</p>

<p style="margin-left:22%;">list the available alternatives
for package &rsquo;foo&rsquo;</p>

<p style="margin-left:11%;">zopen alt &minus;&minus;select
foo</p>

<p style="margin-left:22%;">list the available alternatives
for package &rsquo;foo&rsquo; and allow the user to select
an alternative version</p>

<p style="margin-left:11%;">zopen alt &minus;&minus;set foo
foo&minus;1.2.3.19700101_012345.zos</p>

<p style="margin-left:22%;">set the active version of
package &rsquo;foo&rsquo; to version
foo&minus;1.2.3.19700101_012345.zos if available</p>

<h2>AUTHOR
<a name="AUTHOR"></a>
</h2>


<p style="margin-left:11%; margin-top: 1em">Written by
contributors to the zopen community.
&lt;https://github.com/zopencommunity/meta/graphs/contributors&gt;</p>

<h2>REPORTING BUGS
<a name="REPORTING BUGS"></a>
</h2>


<p style="margin-left:11%; margin-top: 1em">Report bugs at
https://github.com/zopencommunity/meta/issues</p>

<p style="margin-left:11%; margin-top: 1em">This is free
software: you are free to change and redistribute it under
the terms of the Apache License, Version 2.0.
&lt;https://www.apache.org/licenses/LICENSE&minus;2.0.html&gt;
There is NO WARRANTY, to the extent permitted by law.</p>

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
