import json
import os
from django.core.management.base import BaseCommand
from trade.models import GlobalTrainingData, Pairs

class Command(BaseCommand):
    help = 'Import trades from JSON file to GlobalTrainingData (appends, no deletion)'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to JSON file containing trades')

    def handle(self, *args, **options):
        json_file = options.get('file')
        
        if not json_file:
            self.stdout.write(self.style.ERROR('Please provide --file'))
            self.stdout.write('Example: python manage.py import_real_global_data --file=trades.json')
            return
        
        self.import_from_json(json_file)

    def import_from_json(self, json_file):
        """Import from JSON file - appends data, never deletes"""
        
        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f'File not found: {json_file}'))
            return
        
        self.stdout.write(self.style.WARNING(f'Reading JSON file: {json_file}'))
        
        # Read JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            trades_data = json.load(f)
        
        # If it's a single object, wrap in list
        if isinstance(trades_data, dict):
            trades_data = [trades_data]
        
        self.stdout.write(self.style.WARNING(f'Found {len(trades_data)} trades in JSON'))
        
        # Show current count before import
        before_count = GlobalTrainingData.objects.count()
        self.stdout.write(self.style.WARNING(f'Current records in GlobalTrainingData: {before_count}'))
        
        imported = 0
        skipped = 0
        
        for trade in trades_data:
            try:
                # Get pair from pair_id
                pair_id = trade.get('pair_id')
                if not pair_id:
                    self.stdout.write(self.style.WARNING(f'Skipping trade {trade.get("trade_id")}: no pair_id'))
                    skipped += 1
                    continue
                
                pair = Pairs.objects.get(id=pair_id)
                
                # Check if target exists
                target = trade.get('target')
                if target is None:
                    self.stdout.write(self.style.WARNING(f'Trade {trade.get("trade_id")} has no target, skipping'))
                    skipped += 1
                    continue
                
                # Check if trade already exists (optional - prevent duplicates)
                trade_id = trade.get('trade_id')
                if trade_id and GlobalTrainingData.objects.filter(id=trade_id).exists():
                    self.stdout.write(self.style.WARNING(f'Trade {trade_id} already exists, skipping'))
                    skipped += 1
                    continue
                
                GlobalTrainingData.objects.create(
                    pair=pair,
                    momentum_h4=trade.get('momentum_h4'),
                    momentum_h1=trade.get('momentum_h1'),
                    momentum_15m=trade.get('momentum_15m'),
                    momentum_5m=trade.get('momentum_5m'),
                    momentum_1m=trade.get('momentum_1m'),
                    session=trade.get('session'),
                    entry_place=trade.get('entry_place'),
                    buy_or_sell=trade.get('buy_or_sell'),
                    setup_quality=trade.get('setup_quality'),
                    trade_type=trade.get('trade_type'),
                    confirmation=trade.get('confirmation'),
                    mood=trade.get('mood'),
                    tp=trade.get('tp'),
                    tp_reason=trade.get('tp_reason'),
                    risk_reward=trade.get('risk_reward'),
                    target=target,
                    source='initial_real_data'
                )
                imported += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing trade {trade.get("trade_id")}: {e}'))
                skipped += 1
        
        # Show summary
        after_count = GlobalTrainingData.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'✅ Imported {imported} new trades'))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f'⚠️ Skipped {skipped} trades'))
        
        self.show_summary(before_count, after_count)

    def show_summary(self, before_count, after_count):
        wins = GlobalTrainingData.objects.filter(target=1).count()
        losses = GlobalTrainingData.objects.filter(target=0).count()
        total = wins + losses
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'📊 GlobalTrainingData Summary:'))
        self.stdout.write(f'   Before import: {before_count} records')
        self.stdout.write(f'   After import: {after_count} records')
        self.stdout.write(f'   New records added: {after_count - before_count}')
        self.stdout.write(f'   Total records: {total}')
        if total > 0:
            self.stdout.write(f'   Wins: {wins} ({wins/total*100:.1f}%)')
            self.stdout.write(f'   Losses: {losses} ({losses/total*100:.1f}%)')
        self.stdout.write('='*50)