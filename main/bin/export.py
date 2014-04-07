"""
Exports Biostar content into a tab delimited format
"""
__author__ = 'ialbert'
import sys, os, shutil
from main.server import models
pj = os.path.join

def export_users(N, dest, since):
    workdir = pj(dest, "about_me")
    out_name = pj(dest, "users.txt")

    mode = 'at' if since else 'wt'
    out_stream = file(out_name, mode)

    def write(line):
        out_stream.write('%s\n' % line)

    limit = N or None

    fields = "id type status email display_name score scholar my_tags website location date_joined last_visited".split()

    if not os.path.exists(workdir):
        os.makedirs(workdir)

    write("\t".join(fields))

    if since:
        users = models.User.objects.filter(date_joined__gt=since).select_related("profile").order_by('id')
    else:
        users = models.User.objects.all().select_related("profile").order_by('id')[:limit]

    print ("*** found %s users" % users.count() )

    for user in users:
        p = user.profile
        fp = file(pj(workdir, str(user.id)), "wt")
        about_me = p.about_me_html or ''
        website = p.website or ''
        location = p.location or ''
        fp.write(about_me.encode("utf", "replace"))
        fp.close()

        dispay_name = p.display_name.encode("utf", "replace")

        data = [user.id, p.get_type_display(), p.get_status_display(), user.email, p.display_name,
                p.score, p.scholar, p.my_tags, website,  location,
                user.date_joined, p.last_visited,
            ]

        data = map(unicode, data)
        line = u"\t".join(data)
        line = line.encode("utf", "replace")
        write(line)

    print ("*** wrote users into %s" % out_name)

def to_unicode_or_bust(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def export_posts(N, dest, since):
    workdir = pj(dest, "posts")

    out_name = pj(dest, "posts.txt")
    mode = 'at' if since else 'wt'

    out_stream = file(out_name, mode)

    def write(line):
        line = line.encode("utf8")
        out_stream.write('%s\n' % line)

    limit = N or None

    fields = "id root_id parent_id author_id post_type post_status title tag_val " \
        "score full_score views answer_count book_count accepted creation_date lastedit_date lastedit_user url".split()

    if not os.path.exists(workdir):
        os.makedirs(workdir)

    write("\t".join(fields))

    pcount = limit or models.Post.objects.all().count()

    if since:
        posts = models.Post.objects.filter(creation_date__gt=since).order_by('id')
    else:
        posts = models.Post.objects.all().order_by('id')[:limit]

    tags = models.Tag.objects.filter(count__gt=20).order_by("-count")
    if len(tags) < 100:
        tags = models.Tag.objects.all().order_by("-count")[:100]

    tags = map(lambda t: t.name, tags)
    keep = set(tags)

    print ("*** exporting %s posts" % posts.count())

    for index, post in enumerate(posts):

        try:
            # Help gauging the rate of import
            #print ("*** exporting post %s (%2.1f%%)" % (post.id, (100.0 * index/pcount)))
            title = to_unicode_or_bust(post.title)
            title = title.replace("\t", " ")
            html = to_unicode_or_bust(post.html)
            tag_val = to_unicode_or_bust(post.tag_val)

            words = tag_val.split()
            words = filter(lambda w: w in keep, words)
            tag_val = " ".join(words)

            fp = file(pj(workdir, str(post.id)), "wt")
            fp.write(html.encode('utf8'))
            fp.close()

            data = [
                post.id, post.root.id,  post.parent.id, post.author.id,
                post.get_type_display(), post.get_status_display(), title, tag_val,
                post.score, post.full_score, post.views, post.answer_count, post.book_count, post.accepted,
                post.creation_date, post.lastedit_date, post.lastedit_user_id, post.url
            ]

            data = map(unicode, data)
            write("\t".join(data))

        except KeyError, e:
            sys.stderr.write("%s at %s\n" % (e, post.id))

    print ("*** wrote posts into %s" % out_name)

def export_votes(N, dest, since):

    out_name = pj(dest, "votes.txt")
    out_stream = file(out_name, 'wt')

    def write(line):
        out_stream.write('%s\n' % line)

    limit = N or None

    fields = "author_id post_id vote_type vote_date".split()

    write("\t".join(fields))

    votes = models.Vote.objects.all()[:limit]

    print ("*** exporting %s votes" % votes.count())

    for vote in votes:

        data = [
            vote.author.id, vote.post.id, vote.get_type_display(), vote.date
            ]

        data = map(str, data)
        write("\t".join(data))

    print ("*** wrote votes into %s" % out_name)

if __name__ == '__main__':
    import optparse
    from datetime import datetime, timedelta

    usage = "usage: %prog [options]"

    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-u", "--users", dest="users", action="store_true", help="prints the users to the standard out", default=0)
    parser.add_option("-p", "--posts", dest="posts", action="store_true", help="prints the posts to the standard out", default=0)
    parser.add_option("-v", "--votes", dest="votes", action="store_true", help="prints the votes to the standard out", default=0)

    parser.add_option("-n", dest="N", type=int, help="limits to N users", default=0)

    parser.add_option("-w", dest="weeks", type=int, help="limits to last N weeks", default=0)

    parser.add_option("-d", dest="dir",  help="limits to N users", default="~/tmp/biostar-migrate")

    (opts, args) = parser.parse_args()

    opts.dir = os.path.expanduser(opts.dir)

    if opts.weeks:
        since = datetime.now() - timedelta(weeks=opts.weeks)
    else:
        since = None

    # Create the directory if does not exists.
    if not os.path.isdir(opts.dir):
        os.makedirs(opts.dir)

    if opts.users:
        export_users(N=opts.N, dest=opts.dir, since=since)

    if opts.posts:
        export_posts(N=opts.N, dest=opts.dir, since=since)

    if opts.votes:
        export_votes(N=opts.N, dest=opts.dir, since=since)

    print ("*** data exported to: %s" % opts.dir)


