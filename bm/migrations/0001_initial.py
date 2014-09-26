# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.core.management import call_command
from dbtemplates.models import Template

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RegionType'
        db.create_table(u'bm_regiontype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=45)),
        ))
        db.send_create_signal(u'bm', ['RegionType'])

        # Load initial data to bm_region table
        call_command("loaddata", "initial_data.json")

        # Load initial data into db Templates
        if not Template.objects.all().exists():
            call_command("loaddata", "initial_templates.json")
        # Adding model 'Region'
        db.create_table(u'bm_region', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='regions', to=orm['bm.RegionType'])),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bm.Region'], null=True, blank=True)),
        ))
        db.send_create_signal(u'bm', ['Region'])

        # Adding model 'Benchmark'
        db.create_table(u'bm_benchmark', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('start_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='benchmarks', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('min_numbers_of_responses', self.gf('django.db.models.fields.PositiveIntegerField')(default=5)),
            ('_industry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['social.LinkedInIndustry'], null=True, on_delete=models.SET_NULL, db_column='industry_id', blank=True)),
            ('approved', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('popular', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('overview', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'bm', ['Benchmark'])

        # Adding M2M table for field geographic_coverage on 'Benchmark'
        m2m_table_name = db.shorten_name(u'bm_benchmark_geographic_coverage')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('benchmark', models.ForeignKey(orm[u'bm.benchmark'], null=False)),
            ('region', models.ForeignKey(orm[u'bm.region'], null=False))
        ))
        db.create_unique(m2m_table_name, ['benchmark_id', 'region_id'])

        # Adding model 'BenchmarkInvitation'
        db.create_table(u'bm_benchmarkinvitation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('benchmark', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invites', to=orm['bm.Benchmark'])),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invites', to=orm['social.Contact'])),
            ('sent_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('is_allowed_to_forward_invite', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'bm', ['BenchmarkInvitation'])

        # Adding model 'BenchmarkLink'
        db.create_table(u'bm_benchmarklink', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('benchmark', self.gf('django.db.models.fields.related.ForeignKey')(related_name='links', to=orm['bm.Benchmark'])),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=36)),
        ))
        db.send_create_signal(u'bm', ['BenchmarkLink'])

        # Adding model 'Question'
        db.create_table(u'bm_question', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('benchmark', self.gf('django.db.models.fields.related.ForeignKey')(related_name='question', to=orm['bm.Benchmark'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal(u'bm', ['Question'])

        # Adding model 'QuestionResponse'
        db.create_table(u'bm_questionresponse', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='responses', to=orm['bm.Question'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='responses', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'bm', ['QuestionResponse'])

        # Adding model 'QuestionChoice'
        db.create_table(u'bm_questionchoice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='choices', to=orm['bm.Question'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'bm', ['QuestionChoice'])

        # Adding model 'QuestionRanking'
        db.create_table(u'bm_questionranking', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ranks', to=orm['bm.Question'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'bm', ['QuestionRanking'])

        # Adding model 'QuestionOptions'
        db.create_table(u'bm_questionoptions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='options', to=orm['bm.Question'])),
            ('units', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('number_of_decimal', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=2)),
        ))
        db.send_create_signal(u'bm', ['QuestionOptions'])

        # Adding model 'ResponseChoice'
        db.create_table(u'bm_responsechoice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('response', self.gf('django.db.models.fields.related.ForeignKey')(related_name='data_choices', to=orm['bm.QuestionResponse'])),
            ('choice', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bm.QuestionChoice'])),
        ))
        db.send_create_signal(u'bm', ['ResponseChoice'])

        # Adding model 'ResponseRanking'
        db.create_table(u'bm_responseranking', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('response', self.gf('django.db.models.fields.related.ForeignKey')(related_name='data_ranks', to=orm['bm.QuestionResponse'])),
            ('rank', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bm.QuestionRanking'])),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'bm', ['ResponseRanking'])

        # Adding model 'ResponseNumeric'
        db.create_table(u'bm_responsenumeric', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('response', self.gf('django.db.models.fields.related.ForeignKey')(related_name='data_numeric', to=orm['bm.QuestionResponse'])),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'bm', ['ResponseNumeric'])

        # Adding model 'ResponseRange'
        db.create_table(u'bm_responserange', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('response', self.gf('django.db.models.fields.related.ForeignKey')(related_name='data_range', to=orm['bm.QuestionResponse'])),
            ('min', self.gf('django.db.models.fields.IntegerField')()),
            ('max', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'bm', ['ResponseRange'])

        # Adding model 'BenchmarkRating'
        db.create_table(u'bm_benchmarkrating', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('benchmark', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ratings', to=orm['bm.Benchmark'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('rating', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal(u'bm', ['BenchmarkRating'])

        # Adding model 'SeriesStatistic'
        db.create_table(u'bm_seriesstatistic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('benchmark', self.gf('django.db.models.fields.related.ForeignKey')(related_name='series_statistic', to=orm['bm.Benchmark'])),
            ('series', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('sub_series', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'bm', ['SeriesStatistic'])

        # Adding model 'NumericStatistic'
        db.create_table(u'bm_numericstatistic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('benchmark', self.gf('django.db.models.fields.related.ForeignKey')(related_name='numeric_statistic', to=orm['bm.Benchmark'])),
            ('min', self.gf('django.db.models.fields.FloatField')()),
            ('max', self.gf('django.db.models.fields.FloatField')()),
            ('avg', self.gf('django.db.models.fields.FloatField')()),
            ('sd', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'bm', ['NumericStatistic'])


    def backwards(self, orm):
        # Deleting model 'RegionType'
        db.delete_table(u'bm_regiontype')

        # Deleting model 'Region'
        db.delete_table(u'bm_region')

        # Deleting model 'Benchmark'
        db.delete_table(u'bm_benchmark')

        # Removing M2M table for field geographic_coverage on 'Benchmark'
        db.delete_table(db.shorten_name(u'bm_benchmark_geographic_coverage'))

        # Deleting model 'BenchmarkInvitation'
        db.delete_table(u'bm_benchmarkinvitation')

        # Deleting model 'BenchmarkLink'
        db.delete_table(u'bm_benchmarklink')

        # Deleting model 'Question'
        db.delete_table(u'bm_question')

        # Deleting model 'QuestionResponse'
        db.delete_table(u'bm_questionresponse')

        # Deleting model 'QuestionChoice'
        db.delete_table(u'bm_questionchoice')

        # Deleting model 'QuestionRanking'
        db.delete_table(u'bm_questionranking')

        # Deleting model 'QuestionOptions'
        db.delete_table(u'bm_questionoptions')

        # Deleting model 'ResponseChoice'
        db.delete_table(u'bm_responsechoice')

        # Deleting model 'ResponseRanking'
        db.delete_table(u'bm_responseranking')

        # Deleting model 'ResponseNumeric'
        db.delete_table(u'bm_responsenumeric')

        # Deleting model 'ResponseRange'
        db.delete_table(u'bm_responserange')

        # Deleting model 'BenchmarkRating'
        db.delete_table(u'bm_benchmarkrating')

        # Deleting model 'SeriesStatistic'
        db.delete_table(u'bm_seriesstatistic')

        # Deleting model 'NumericStatistic'
        db.delete_table(u'bm_numericstatistic')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'bm.benchmark': {
            'Meta': {'object_name': 'Benchmark'},
            '_industry': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['social.LinkedInIndustry']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'db_column': "'industry_id'", 'blank': 'True'}),
            'approved': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'geographic_coverage': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'benchmarks'", 'symmetrical': 'False', 'to': u"orm['bm.Region']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_numbers_of_responses': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'overview': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'benchmarks'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'popular': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'bm.benchmarkinvitation': {
            'Meta': {'object_name': 'BenchmarkInvitation'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invites'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed_to_forward_invite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invites'", 'to': u"orm['social.Contact']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'sent_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'bm.benchmarklink': {
            'Meta': {'object_name': 'BenchmarkLink'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '36'})
        },
        u'bm.benchmarkrating': {
            'Meta': {'object_name': 'BenchmarkRating'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ratings'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rating': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'})
        },
        u'bm.numericstatistic': {
            'Meta': {'object_name': 'NumericStatistic'},
            'avg': ('django.db.models.fields.FloatField', [], {}),
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'numeric_statistic'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max': ('django.db.models.fields.FloatField', [], {}),
            'min': ('django.db.models.fields.FloatField', [], {}),
            'sd': ('django.db.models.fields.FloatField', [], {})
        },
        u'bm.question': {
            'Meta': {'object_name': 'Question'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question'", 'to': u"orm['bm.Benchmark']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'bm.questionchoice': {
            'Meta': {'object_name': 'QuestionChoice'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'choices'", 'to': u"orm['bm.Question']"})
        },
        u'bm.questionoptions': {
            'Meta': {'object_name': 'QuestionOptions'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_decimal': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': u"orm['bm.Question']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'bm.questionranking': {
            'Meta': {'object_name': 'QuestionRanking'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ranks'", 'to': u"orm['bm.Question']"})
        },
        u'bm.questionresponse': {
            'Meta': {'object_name': 'QuestionResponse'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': u"orm['bm.Question']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"})
        },
        u'bm.region': {
            'Meta': {'object_name': 'Region'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bm.Region']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'regions'", 'to': u"orm['bm.RegionType']"})
        },
        u'bm.regiontype': {
            'Meta': {'object_name': 'RegionType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'bm.responsechoice': {
            'Meta': {'object_name': 'ResponseChoice'},
            'choice': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bm.QuestionChoice']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_choices'", 'to': u"orm['bm.QuestionResponse']"})
        },
        u'bm.responsenumeric': {
            'Meta': {'object_name': 'ResponseNumeric'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_numeric'", 'to': u"orm['bm.QuestionResponse']"}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        u'bm.responserange': {
            'Meta': {'object_name': 'ResponseRange'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max': ('django.db.models.fields.IntegerField', [], {}),
            'min': ('django.db.models.fields.IntegerField', [], {}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_range'", 'to': u"orm['bm.QuestionResponse']"})
        },
        u'bm.responseranking': {
            'Meta': {'object_name': 'ResponseRanking'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rank': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bm.QuestionRanking']"}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_ranks'", 'to': u"orm['bm.QuestionResponse']"}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        u'bm.seriesstatistic': {
            'Meta': {'object_name': 'SeriesStatistic'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'series_statistic'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'series': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sub_series': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'social.company': {
            'Meta': {'object_name': 'Company'},
            '_industry': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'companies'", 'db_column': "'industry_id'", 'on_delete': 'models.SET_NULL', 'to': u"orm['social.LinkedInIndustry']", 'blank': 'True', 'null': 'True'}),
            'code': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'social.contact': {
            'Meta': {'unique_together': "(('code', 'provider'),)", 'object_name': 'Contact'},
            '_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'db_column': "'email'", 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'employees'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['social.Company']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'headline': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'contacts'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['bm.Region']"}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'contacts'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'provider': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        u'social.linkedinindustry': {
            'Meta': {'object_name': 'LinkedInIndustry'},
            'code': ('django.db.models.fields.PositiveSmallIntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['bm']