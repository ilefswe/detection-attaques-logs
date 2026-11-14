package securite;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.GenericOptionsParser;

/**
 * Usage :
 *   hadoop jar securite-logs-1.jar securite.LogDriver [-D seuil=N] <input> <output> <mode>
 *   mode = ip | statut | bruteforce | scan | attaques
 */
public class LogDriver {

    public static void main(String[] args) throws Exception {
        Configuration conf = new Configuration();
        // Accepte les options Hadoop (-D seuil=50 ...) avant les arguments du programme
        args = new GenericOptionsParser(conf, args).getRemainingArgs();
        if (args.length < 3) {
            System.err.println("Usage: LogDriver [-D seuil=N] <input> <output> <ip|statut|bruteforce|scan|attaques>");
            System.exit(2);
        }
        String mode = args[2];
        conf.set("mode", mode);
        // Seuil d'alerte par défaut : 20 pour bruteforce et scan, 1 (tout afficher) sinon
        if (conf.get("seuil") == null) {
            conf.setInt("seuil", (mode.equals("bruteforce") || mode.equals("scan")) ? 20 : 1);
        }

        Job job = Job.getInstance(conf, "Analyse de logs - " + mode);
        job.setJarByClass(LogDriver.class);

        job.setMapperClass(LogMapper.class);
        job.setCombinerClass(SommeCombiner.class);
        job.setReducerClass(AlerteReducer.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
