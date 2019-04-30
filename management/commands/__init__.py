
class ProgressBarMixin:
    def print_progress_bar(self, iteration, total, **kwargs):
        """
        From http://stackoverflow.com/a/34325723/2575355

        Call in a loop to create terminal progress bar
        @params:
            iteration - Required: current iteration (Int)
            total     - Required: total iterations (Int)
            prefix    - Optional: prefix string (Str)
            suffix    - Optional: suffix string (Str)
            decimals  - Optional: number of decimals in % complete (Int)
            length    - Optional: character length of bar (Int)
            fill      - Optional: bar fill character (Str)
        """
        prefix = kwargs.get('prefix', '')
        suffix = kwargs.get('suffix', '')
        decimals = kwargs.get('decimals', 1)
        length = kwargs.get('length', 100)
        fill = kwargs.get('fill', '█')
        percent = ("{0:." + str(decimals) + "f}").format(
            100 * (iteration / float(total))
        )
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        self.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix),
                          ending='\r')
        # Print New Line on Complete
        if iteration == total:
            self.stdout.write('')
