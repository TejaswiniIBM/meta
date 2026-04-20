<div v-pre class="man-page-content">


<h1 align="center">ZOPEN-USAGE</h1>




<h2>NAME
<a name="NAME"></a>
</h2>


<p style="margin-left:11%; margin-top: 1em">zopen-usage
&minus; manual page for zopen-usage 0.8.4</p>

<h2>SYNOPSIS
<a name="SYNOPSIS"></a>
</h2>



<p style="margin-left:11%; margin-top: 1em"><b>zopen-usage</b>
[<i>OPTION</i>] [<i>ZOPEN_ROOTFS</i>]
[<i>PARAMETERS</i>]...</p>

<h2>DESCRIPTION
<a name="DESCRIPTION"></a>
</h2>



<p style="margin-left:11%; margin-top: 1em">zopen&minus;usage
is a utility to display the file system usage by a zopen
environment</p>

<h2>OPTIONS
<a name="OPTIONS"></a>
</h2>


<table width="100%" border="0" rules="none" frame="void"
       cellspacing="0" cellpadding="0">
<tr valign="top" align="left">
<td width="11%"></td>
<td width="7%">


<p style="margin-top: 1em"><b>&minus;&minus;pie</b></p></td>
<td width="4%"></td>
<td width="60%">


<p style="margin-top: 1em">generate a pie chart showing
space hogs</p></td>
<td width="18%">
</td></tr>
</table>

<p style="margin-left:11%;"><b>&minus;h</b>,
<b>&minus;&minus;help</b>, &minus;?</p>

<p style="margin-left:22%;">display this help and exit.</p>

<p style="margin-left:11%;"><b>&minus;v</b>,
<b>&minus;&minus;verbose</b></p>

<p style="margin-left:22%;">run in verbose mode.</p>


<p style="margin-left:11%;"><b>&minus;&minus;version</b></p>

<p style="margin-left:22%;">print version</p>

<h2>EXAMPLES
<a name="EXAMPLES"></a>
</h2>


<p style="margin-left:11%; margin-top: 1em">zopen usage</p>

<p style="margin-left:22%;">list the file system usage for
the environment</p>

<p style="margin-left:11%;">zopen usage &minus;&minus;pie
/mnt/zopen</p>

<p style="margin-left:22%;">list the file system usage for
the zopen environment at the mount point /mnt/zopen</p>


<p style="margin-left:11%; margin-top: 1em"><b>Notes:</b></p>

<p style="margin-left:22%;">Values might not add to 100%
due to rounding during calculations; use the reported values
as guidance, rounding up for capacity planning for
example.</p>

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
