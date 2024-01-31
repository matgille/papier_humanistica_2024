<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs" version="2.0">
    <xsl:output method="text"/>
    <xsl:strip-space elements="*"/>

    <xsl:template match="table">
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="tr[count(descendant::a[@href != '']) = 1]"/>


    <xsl:template match="tr[count(descendant::a[@href != '']) &gt; 1]">
        <xsl:for-each select="descendant::td[a[@href != '']]">
            <xsl:value-of select="a[@href != '']/@href"/>
            <xsl:text>&#009;</xsl:text>
        </xsl:for-each>
        <xsl:if test="following::tr[count(descendant::a[@href != '']) &gt; 1]">
            <xsl:text>&#10;</xsl:text>
        </xsl:if>
    </xsl:template>
</xsl:stylesheet>
